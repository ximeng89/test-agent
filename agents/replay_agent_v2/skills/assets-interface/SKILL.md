---
name: "assets-interface"
description: "从Assets系统搜索并下载产品图片到本地缓存。用于Lookbook自动生成Pipeline的第5步，接收从PLM系统查询获取的SKU列表，搜索并下载产品图片到本地缓存目录，"
metadata:
  openclaw:
    requires:
      bins: ["python"]
---

## 核心功能

- **图片搜索**：通过完整SAP编码搜索Assets系统中的图片（精确匹配）
- **图片下载**：下载搜索到的匹配图片（一对一关系）
- **缓存管理**：自动管理已下载的图片，避免重复下载
- **批量处理**：支持批量处理多个SKU的图片下载
- **数据整合**：将图片URL与SKU信息整合输出
- **SAP编码支持**：只接受完整SAP编码格式（含竖线分隔符），进行精确搜索

## 环境变量配置

| 环境变量 | 是否必需 | 默认值 | 说明 |
|----------|----------|--------|------|
| `ASSETS_API_BASE_URL` | 否 | `http://47.97.118.146:14000` | Assets API基础地址 |
| `ASSETS_FIELD_ID` | 否 | `2049335970058342400` | SKU/code字段的数字ID（NOT_ENUM类型） |
| `ASSETS_SAP_FIELD_ID` | 否 | 无 | SAP编码字段的数字ID（可选，用于codesapr3搜索） |
| `ASSETS_FOLDER_ID` | 否 | `"0"` | 默认搜索的文件夹ID（"0"表示/Home目录） |

## 搜索方式

### 支持的搜索关键字
- **codesapr3**：完整SAP编码（必需，格式如 `M0972|.000.156|23A`）

> **重要**：从PLM系统获取的SKU列表中，应使用 `codesapr3` 字段（完整SAP编码）进行搜索，而非普通 `code` 字段。

### API接口信息
- **接口地址**：`http://47.97.118.146:14000/typekey/api/v1/openapi/assets/search/structured`
- **请求方式**：POST
- **认证方式**：无需认证（当前配置）
- **查询模式**：LITE
- **匹配方式**：精确匹配（一对一）

### 输入编码格式要求

| 输入类型 | 格式要求 | 示例 | 是否支持 |
|----------|----------|------|----------|
| 完整SAP编码 | 包含竖线分隔符 | `M0972|.000.156|23A` | ✅ 支持 |
| 普通code | 不包含竖线 | `M0972` | ❌ 不支持 |

> **注意**：系统强制要求输入完整SAP编码格式。如果输入普通code（不含竖线），会抛出错误：`ValueError: 输入必须是完整SAP编码格式（如M0972|.000.156|23A）`

## Assets API LITE模式说明

LITE模式只使用以下三个字段：
- **folderIdList**：目录ID列表（空数组表示搜索全部目录）
- **tagLogicType**：标签逻辑类型（AND/OR）
- **tagConditionList**：标签条件列表

支持的元数据字段类型：
- SINGLE_SELECT
- MULTI_SELECT  
- NOT_ENUM

不支持：
- STRING
- TIME
- NUMBER
- PRO模式的复杂条件树

## 输入格式

### 格式一：接收 plm-interface 的输出（推荐）

```json
{
  "success": true,
  "sku_list": [
    {
      "code": "00W2",
      "codesapr3": "M00W2|.000.483|07R",
      "decode_category": {"code": "PL", "description": "PANTS"},
      "s01modcoldata_decode_color": [{"code": "", "description": "BLACK"}]
    },
    {
      "code": "12OC",
      "codesapr3": "M12OC|.000.2223EG",
      "decode_category": {"code": "PL", "description": "PANTS"},
      "s01modcoldata_decode_color": [{"code": "", "description": "BLUE"}]
    }
  ],
  "total_count": 2
}
```

> **重要**：系统会自动从 `sku_list` 的每个元素中提取 `codesapr3` 字段（完整SAP编码）进行搜索。

### 格式二：SAP编码列表

```json
{
  "codes": ["M00W2|.000.483|07R", "M12OC|.000.2223EG", "M13LZ|.000.00L05G"]
}
```

### 格式三：带额外信息的输入

```json
{
  "codes": ["M00W2|.000.483|07R", "M12OC|.000.2223EG"],
  "items_info": [
    {"code": "M00W2|.000.483|07R", "color": "Black", "category": "PANTS", "batch_id": "batch_1", "batch_index": 1},
    {"code": "M12OC|.000.2223EG", "color": "Blue", "category": "PANTS", "batch_id": "batch_1", "batch_index": 3}
  ]
}
```

### 格式四：SKU列表（兼容旧格式）

```json
[
  {"code": "00W2", "codesapr3": "M00W2|.000.483|07R"},
  {"code": "12OC", "codesapr3": "M12OC|.000.2223EG"}
]
```

> **注意**：系统会优先使用 `codesapr3` 字段进行搜索，如果不存在则使用 `code` 字段。但 `code` 字段必须是完整SAP编码格式。

## 输出格式

```json
{
  "items": [
    {
      "id": "A1",
      "code": "M00W2|.000.483|07R",
      "imgUrl": "https://assets-api.example.com/api/file/download?fileId=xxx&token=xxx",
      "metadata": {
        "code": "00W2",
        "codesapr3": "M00W2|.000.483|07R",
        "decode_category": "PANTS",
        "decode_xvestibilita": "REGULAR",
        "s01modcoldata_decode_color": "BLACK",
        "decode_material": "COTTON TWILL",
        "decode_xtipomat": "Twill",
        "decode_xtreatment": "WASH",
        "decode_xvarfabr": "Generico",
        "fstampa": false,
        "flavaggio": true
      },
      "batch_id": "batch_1",
      "batch_index": 1
    },
    {
      "id": "A2",
      "code": "M12OC|.000.2223EG",
      "imgUrl": "https://assets-api.example.com/api/file/download?fileId=yyy&token=yyy",
      "metadata": {
        "code": "12OC",
        "codesapr3": "M12OC|.000.2223EG",
        "decode_category": "PANTS",
        "decode_xvestibilita": "SLIM",
        "s01modcoldata_decode_color": "BLUE",
        "decode_material": "STRETCH PIQUET",
        "decode_xtipomat": "Piquet",
        "decode_xtreatment": "GARMENT DYED",
        "decode_xvarfabr": "Generico",
        "fstampa": true,
        "flavaggio": false
      },
      "batch_id": "batch_1",
      "batch_index": 2
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 图片项列表 |
| items[].id | string | 唯一标识（如 A1, A2, B1...） |
| items[].code | string | **完整SAP编码**（如 `M00W2|.000.483|07R`） |
| items[].imgUrl | string | **云端图片URL**（可直接在浏览器打开查看） |
| items[].metadata | object | 包含所有PLM字段的扁平结构对象 |
| items[].batch_id | string | 批次ID |
| items[].batch_index | number | 批次内序号 |

### imgUrl获取说明

`imgUrl` 字段返回的是云端图片的 **presignUrl**（预签名URL），获取方式如下：

1. **API调用**：通过Assets系统API搜索资产时，每个资产对象包含 `presignUrl` 字段
2. **URL格式**：完整的HTTP/HTTPS URL，可直接在浏览器中打开查看图片
3. **URL优先级**：
   - 优先使用 `presignUrl` 字段（API返回的临时访问链接）
   - 若不存在，依次尝试 `url`、`fileUrl`、`downloadUrl`、`imageUrl`、`path` 字段
4. **访问方式**：直接复制 `imgUrl` 的值到浏览器地址栏即可查看图片

**示例imgUrl**：
```
https://47.97.118.146:14000/api/file/download?fileId=xxx&token=xxx
```

> **注意**：presignUrl通常有有效期限制（如1小时），过期后需要重新获取。

### metadata字段说明

`metadata` 字段包含从PLM系统获取的所有可用字段，采用扁平结构存储，**直接从plm-interface的输出中提取并扁平化**：

| PLM字段 | 说明 | 示例值 |
|---------|------|--------|
| code | SKU编码 | "00W2" |
| codesapr3 | SAP编码 | "M00W2|.000.483|07R" |
| decode_category | 品类（取description值） | "PANTS" |
| decode_xvestibilita | 版型（取description值） | "SLIM" |
| s01modcoldata_decode_color | 颜色（取第一个元素的description值） | "BLACK" |
| decode_material | 材质（取title值） | "DS00IR200Z BF3814 BLACK - 483" |
| decode_xtipomat | 材质类型（取description值） | "Denim" |
| decode_xtreatment | 处理工艺（取description值） | "RESINA+RINSE WASH+ASCIUGATURA APPESA" |
| decode_xvarfabr | 面料特征（取description值） | "Strech" |
| fstampa | 印花标识 | false |
| flavaggio | 水洗标识 | true |
| decode_season | 季节（取description值） | "Autunno Inverno 2026" |
| decode_gender | 性别（取description值） | "MAN" |

**metadata字段处理规则**：
- **嵌套字典类型**：优先提取 `description` 字段，其次 `title`，最后 `code` 字段
- **列表类型**（如颜色列表）：提取第一个元素的 `description` 字段
- **基本类型**（字符串、数字、布尔值）：直接保留
- **完整PLM对象传递**：从plm-interface的sku_list中的每个SKU对象完整传递，确保所有字段都被处理

### ID 和批次生成规则

#### `id` 字段生成规则
`id` 字段采用 **字母+数字** 的格式，用于唯一标识每个图片项：
- **字母部分**：表示批次组（A、B、C...），每32个图片为一个批次组
- **数字部分**：表示批次组内的序号（1-32）

**示例**：
- 第1-32个图片：`A1`, `A2`, ..., `A32`
- 第33-64个图片：`B1`, `B2`, ..., `B32`
- 第65-96个图片：`C1`, `C2`, ..., `C32`

#### `batch_id` 字段生成规则
`batch_id` 表示图片所属的批次，格式为 `batch_{批次号}`：
- 每32个图片为一个批次
- 批次号从1开始递增

**示例**：
- 第1-32个图片：`batch_1`
- 第33-64个图片：`batch_2`
- 第65-96个图片：`batch_3`

#### `batch_index` 字段生成规则
`batch_index` 表示图片在当前批次内的序号：
- 在每个批次内从1开始递增
- 达到32后重置为1，进入下一个批次

**示例**：
- 第1个图片：`batch_index: 1`，`batch_id: batch_1`
- 第32个图片：`batch_index: 32`，`batch_id: batch_1`
- 第33个图片：`batch_index: 1`，`batch_id: batch_2`

#### 计算逻辑公式

```
总序号 = 图片在列表中的位置（从1开始）
批次号 = ceil(总序号 / 32)
批次组字母 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[批次号 - 1]
batch_id = f"batch_{批次号}"
batch_index = ((总序号 - 1) % 32) + 1
id = f"{批次组字母}{batch_index}"
```

**示例计算**：
- 第1个图片：批次号=1，批次组字母=A，id=A1，batch_id=batch_1，batch_index=1
- 第32个图片：批次号=1，批次组字母=A，id=A32，batch_id=batch_1，batch_index=32
- 第33个图片：批次号=2，批次组字母=B，id=B1，batch_id=batch_2，batch_index=1
- 第64个图片：批次号=2，批次组字母=B，id=B32，batch_id=batch_2，batch_index=32

## 使用方式

### 方式一：命令行参数（单个SAP编码）

```bash
python scripts/get_assets.py --code "M13LZ|.000.00L05G"
```

### 方式二：命令行参数（SAP编码列表）

```bash
python scripts/get_assets.py --codes '["M00W2|.000.483|07R", "M12OC|.000.2223EG"]'
```

### 方式三：输入JSON文件

```bash
python scripts/get_assets.py input.json
```

input.json内容：
```json
[
  {"code": "00W2", "codesapr3": "M00W2|.000.483|07R"},
  {"code": "12OC", "codesapr3": "M12OC|.000.2223EG"}
]
```

### 方式四：标准输入

```bash
echo '["M00W2|.000.483|07R", "M12OC|.000.2223EG"]' | python scripts/get_assets.py
```

## 约束与注意事项

### 认证要求
- 无需认证（当前配置），通过code元数据字段搜索图片

### 网络依赖
- 需要能够访问Assets系统API：`http://47.97.118.146:14000`

### 缓存机制
- 自动缓存已下载的图片，避免重复下载
- 缓存目录：`./assets/`

### 错误处理
- 如果任何步骤失败，应向用户报告错误并停止执行
- **不要**修改Assets系统中的任何数据，只做搜索和下载操作
- **不要**重复下载已缓存的图片
- 如果下载失败，直接报告错误信息，但继续尝试下载其他图片
- 使用LITE模式查询，仅支持SINGLE_SELECT、MULTI_SELECT、NOT_ENUM类型的元数据字段

## 输入输出示例

### ⚠️ 强制路径规范（任务隔离）

> **重要**：必须使用任务隔离路径，每个任务使用独立的输入输出目录，避免任务之间相互干扰。

| 类型 | 路径格式 | 说明 |
|------|----------|------|
| **输入文件** | `tasks/{task_id}/output/plm-interface/output.json` | 接收 plm-interface 技能的输出 JSON |
| **输出文件** | `tasks/{task_id}/output/assets-interface/output.json` | 输出产品图片URL和SKU信息 |


## 📥 输入

接收 **plm-interface** 技能的输出 JSON，包含SKU列表和PLM metadata。

**输入JSON示例**：
```json
{
  "success": true,
  "sku_list": [
    {"code": "00W2", "codesapr3": "M00W2|.000.483|07R", "decode_category": {"code": "PL", "description": "PANTS"}},
    {"code": "12OC", "codesapr3": "M12OC|.000.2223EG", "decode_category": {"code": "PL", "description": "PANTS"}}
  ],
  "total_count": 2
}
```

## 📤 输出

输出包含产品图片URL和SKU信息的结构化JSON，每个产品包含完整的PLM metadata（品类、颜色、材质等）。

**输出JSON示例**：
```json
{
  "items": [
    {
      "id": "A1",
      "code": "M00W2|.000.483|07R",
      "imgUrl": "http://basil.oss-cn-hangzhou.aliyuncs.com/assets/0/xxx/xxx.jpg?Expires=xxx&OSSAccessKeyId=xxx&Signature=xxx",
      "metadata": {
        "code": "00W2",
        "codesapr3": "M00W2|.000.483|07R",
        "decode_category": "PANTS"
      },
      "batch_id": "batch_1",
      "batch_index": 1
    },
    {
      "id": "A2",
      "code": "M12OC|.000.2223EG",
      "imgUrl": "http://basil.oss-cn-hangzhou.aliyuncs.com/assets/0/yyy/yyy.jpg?Expires=xxx&OSSAccessKeyId=xxx&Signature=xxx",
      "metadata": {
        "code": "12OC",
        "codesapr3": "M12OC|.000.2223EG",
        "decode_category": "PANTS"
      },
      "batch_id": "batch_1",
      "batch_index": 2
    }
  ]
}
```

### SAP编码格式要求

系统**强制要求**输入必须是完整SAP编码格式：

| 格式要求 | 说明 |
|----------|------|
| **必须包含竖线分隔符** | 如 `M0972|.000.156|23A` |
| **格式示例** | `M{code}|.{variant}.{option}|{color}` |
| **匹配方式** | 精确匹配（一对一） |

**错误情况**：
- 输入 `M0972`（普通code）→ 抛出错误：`ValueError: 输入必须是完整SAP编码格式（如M0972|.000.156|23A）`

**正确情况**：
- 输入 `M0972|.000.156|23A`（完整SAP编码）→ 成功搜索到对应的资产

## 技能组合模式

### 标准Lookbook生成（推荐）
```
sku-filter-analysis → plm-interface → assets-interface
```

### 已知SKU直接下载图片
```
assets-interface（直接传入产品code列表或媒体ID列表）
```

## 脚本

- `scripts/get_assets.py`：Assets系统图片搜索下载主脚本

## Lookbook报告格式（输出结果示例）

```markdown
# Lookbook 报告：FW26 RTW

## 筛选条件
- 季节：FW26 (262)
- 部门：RTW外套 (001)
- 状态：样品
- 策略：高毛利重点推广

## 产品列表

### KU103D - 男士休闲外套
![KU103D](/path/to/image.jpg)
- SAP编码：123456789
- 材质：羊毛混纺
- 颜色：黑色
- 版型：Regular

### KU104E - 女士风衣
![KU104E](/path/to/image.jpg)
- SAP编码：987654321
- 材质：棉质
- 颜色：米色
- 版型：Normal

## 统计信息
- 共查询到：15个SKU
- 成功下载：15张图片
- 生成时间：2026-04-28
```