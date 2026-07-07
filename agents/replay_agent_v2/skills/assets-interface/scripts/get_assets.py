#!/usr/bin/env python3
"""
资产图片获取技能 - 通过Assets API搜索并下载图片

功能：
1. 通过code元数据搜索Assets系统中的图片（LITE模式）
2. 下载图片到本地缓存
3. 支持批量搜索和下载
4. **完整保留PLM元数据**：从plm-interface输出中提取完整的SKU信息并扁平化到metadata字段

环境变量要求：
- ASSETS_API_BASE_URL: Assets API基础地址（默认：http://47.97.118.146:14000）
- ASSETS_FIELD_ID: SKU/code字段的fieldId（必需，用于结构化搜索）

API参考文档：
- Assets相关API.docx
- 资产搜索 LITE 模式调用示例.docx

LITE模式规范：
- 只使用三个字段：folderIdList, tagLogicType, tagConditionList
- conditionGroupList必须保持空数组
- 支持的元数据字段类型：SINGLE_SELECT, MULTI_SELECT, NOT_ENUM
- 不支持：STRING, TIME, NUMBER
- tagLogicType只支持 AND 或 OR
- 枚举字段的value传optionId，非枚举字段传实际值
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Any, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AssetClient:
    def __init__(self):
        """初始化资产客户端"""
        # Assets API基础地址（支持环境变量配置）
        self.base_url = os.getenv("ASSETS_API_BASE_URL", "http://47.97.118.146:14000")
        
        # SKU/code字段的fieldId（支持环境变量配置，默认值：2049335970058342400）
        self.field_id = os.getenv("ASSETS_FIELD_ID", "2049335970058342400")
        
        # SAP编码字段的fieldId（可选，用于codesapr3搜索）
        self.sap_field_id = os.getenv("ASSETS_SAP_FIELD_ID")
        
        # 默认文件夹ID（支持环境变量配置，默认0表示/Home目录）
        self.default_folder_id = os.getenv("ASSETS_FOLDER_ID", "0")
        
        # 本地缓存目录（符合OpenClaw规范）
        self.cache_dir = os.path.expanduser("~/.openclaw/cache/assets")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # API端点定义（根据文档）
        self.endpoints = {
            "folder_tree": "/typekey/api/v1/openapi/assets/folder/file/tree",
            "folder_optional": "/typekey/api/v1/openapi/assets/folder/tree",
            "structured_search": "/typekey/api/v1/openapi/assets/search/structured"
        }

    def get_folder_file_tree(self) -> Dict[str, Any]:
        """
        获取Assets所有或特定目录层级的文件夹&文件树状信息
        
        Returns:
            文件夹树结构
        """
        url = f"{self.base_url}{self.endpoints['folder_tree']}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_folder_optional(self) -> Dict[str, Any]:
        """
        获取文件夹目录层级（下拉列表）
        
        Returns:
            文件夹层级列表
        """
        url = f"{self.base_url}{self.endpoints['folder_optional']}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def _validate_lite_params(self, code: str) -> None:
        """
        验证LITE模式参数
        
        Args:
            code: 搜索的code值
        
        Raises:
            ValueError: 参数验证失败时
        """
        if not self.field_id:
            raise ValueError("未配置ASSETS_FIELD_ID环境变量，请联系管理员获取SKU字段的fieldId")
        
        if not code or not isinstance(code, str):
            raise ValueError("code参数必须是非空字符串")

    def _is_sap_code(self, code: str) -> bool:
        """
        判断是否为SAP编码格式
        
        SAP编码格式通常包含竖线分隔符，如：M13LZ|.000.00L05G, M00W2|.000.483|07R
        
        Args:
            code: 待判断的编码
            
        Returns:
            是否为SAP编码格式
        """
        return "|" in code
    
    def _build_tag_conditions(self, code: str) -> List[Dict[str, Any]]:
        """
        构建标签条件列表
        
        根据code格式构建搜索条件：
        - 如果是完整SAP编码（包含|），使用完整编码进行精确搜索
        - 如果不是SAP编码格式，抛出错误（根据需求，必须提供完整SAP编码）
        
        输入输出示例：
        - 输入: M0972|.000.156|23A -> 搜索 sku_code="M0972|.000.156|23A"
        - 输入: M13LZ|.000.00L05G -> 搜索 sku_code="M13LZ|.000.00L05G"
        
        Args:
            code: 产品code（必须是完整SAP编码格式）
            
        Returns:
            标签条件列表
            
        Raises:
            ValueError: 如果输入不是完整SAP编码格式
        """
        conditions = []
        
        # 获取完整SAP编码
        search_value = str(code)
        
        # 根据需求：必须是完整SAP编码格式（包含|），否则抛出错误
        if not self._is_sap_code(code):
            raise ValueError(f"输入必须是完整SAP编码格式（如M0972|.000.156|23A），当前输入: {code}")
        
        # 添加sku_code字段搜索条件（精确匹配完整SAP编码）
        conditions.append({
            "fieldId": self.field_id,
            "value": [search_value]
        })
        
        # 如果配置了SAP字段ID，添加SAP编码搜索条件
        if self.sap_field_id:
            conditions.append({
                "fieldId": self.sap_field_id,
                "value": [str(code)]
            })
        
        return conditions
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def search_by_code(self, code: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        通过code元数据搜索资产（使用LITE模式结构化搜索）
        
        根据文档：
        - LITE模式只使用三个字段：folderIdList, tagLogicType, tagConditionList
        - conditionGroupList必须保持空数组
        - tagLogicType只支持 AND 或 OR
        - NOT_ENUM类型字段的value必须是数组格式
        
        Args:
            code: 产品code（必须是完整SAP编码格式，如M13LZ|.000.00L05G）
            folder_id: 目录ID，默认使用环境变量配置的值或"0"（/Home目录）
        
        Returns:
            匹配的资产列表（所有匹配结果，不再只取第一个）
        """
        # 验证参数
        self._validate_lite_params(code)
        
        # 使用传入的folder_id或默认值
        actual_folder_id = folder_id if folder_id is not None else self.default_folder_id
        
        url = f"{self.base_url}{self.endpoints['structured_search']}"
        
        # LITE模式请求体（严格按照文档规范）
        # 根据code类型构建搜索条件
        tag_conditions = self._build_tag_conditions(code)
        
        payload = {
            "folderIdList": [actual_folder_id] if actual_folder_id else [],
            "tagLogicType": "OR",
            "tagConditionList": tag_conditions,
            "conditionGroupList": []  # LITE模式必须为空数组
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 处理响应格式
        if isinstance(data, dict):
            # API通常返回 {"success": true/false, "data": {...}, "message": "..."} 格式
            if "success" in data and not data["success"]:
                error_msg = data.get("message", "未知错误")
                raise ValueError(f"API返回错误: {error_msg} (完整响应: {json.dumps(data)})")
            
            assets = data.get("data", {}).get("fileList", []) if isinstance(data.get("data"), dict) else data.get("data", [])
            
            return assets
        
        return data if isinstance(data, list) else []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def download_image(self, image_url: str, save_path: Optional[str] = None) -> str:
        """
        下载图片到本地缓存
        
        Args:
            image_url: 图片URL（支持相对路径和绝对路径）
            save_path: 保存路径（可选，默认缓存目录）
        
        Returns:
            本地保存路径
        """
        # 如果URL是相对路径，添加基础URL
        if not image_url.startswith(("http://", "https://")):
            image_url = f"{self.base_url}{image_url}"
        
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()

        # 获取Content-Type确定文件扩展名
        content_type = response.headers.get("Content-Type", "image/jpeg")
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp"
        }
        ext = ext_map.get(content_type, ".jpg")

        # 从URL提取文件名或生成唯一文件名
        if not save_path:
            file_name = os.path.basename(image_url).split("?")[0]
            # 清理文件名，确保安全
            file_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
            if not file_name or len(file_name) > 100:
                file_name = f"{int(time.time())}_{hash(image_url)}{ext}"
            save_path = os.path.join(self.cache_dir, file_name)

        # 保存文件
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return save_path

    def _get_image_url(self, asset: Dict[str, Any]) -> Optional[str]:
        """
        从资产对象中提取图片URL
        
        根据API文档，优先使用presignUrl字段
        
        Args:
            asset: 资产对象
            
        Returns:
            图片URL，如果找不到返回None
        """
        # 根据API文档，优先使用presignUrl字段
        if "presignUrl" in asset:
            return asset["presignUrl"]
        
        # fallback到其他常见字段
        fallback_fields = ["url", "fileUrl", "downloadUrl", "imageUrl", "path"]
        for field in fallback_fields:
            if field in asset:
                return asset[field]
        
        # 尝试嵌套结构
        if "data" in asset and isinstance(asset["data"], dict):
            if "presignUrl" in asset["data"]:
                return asset["data"]["presignUrl"]
            for field in fallback_fields:
                if field in asset["data"]:
                    return asset["data"][field]
        
        return None
    
    def search_and_download_v2(self, codes: List[str], code_info_map: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        批量搜索并下载图片（返回新格式：{"items": [...]}）
        
        Args:
            codes: code列表（用于搜索资产）
            code_info_map: code到额外信息的映射，包含color, category, batch_id, batch_index, metadata
        
        Returns:
            下载结果，格式为 {"items": [...]}，每个item包含：
            - id: 唯一标识（如 A1, A2, B1...）
            - code: SKU编码
            - imgUrl: 云端图片URL
            - metadata: 包含所有PLM字段的扁平结构对象（**关键改进：完整保留PLM数据**）
            - batch_id: 批次ID
            - batch_index: 批次内序号
        """
        items = []
        total_item_count = 0
        
        for code in codes:
            try:
                # 获取code的额外信息（包含完整的PLM metadata）
                info = code_info_map.get(code, {}) if code_info_map else {}
                
                # **关键改进**：直接从info中获取完整的PLM原始数据
                plm_original_data = info.get("original_plm_data", {})
                
                # 搜索资产（返回所有匹配结果）
                assets = self.search_by_code(code)
                
                if not assets or len(assets) == 0:
                    continue
                
                # 遍历所有匹配的资产
                for asset in assets:
                    try:
                        # 获取图片URL（云端presignUrl）
                        image_url = self._get_image_url(asset)
                        
                        if not image_url:
                            continue
                        
                        # 计算总序号（用于生成ID和批次）
                        total_item_count += 1
                        
                        # 计算批次号和批次内序号（每32个为一批）
                        batch_number = (total_item_count - 1) // 32 + 1
                        batch_index = (total_item_count - 1) % 32 + 1
                        
                        # 计算批次字母（A-Z循环）
                        batch_letter = chr(ord('A') + (batch_number - 1))
                        if batch_letter > 'Z':
                            batch_letter = 'A'
                        
                        # 生成唯一ID（如 A1, A2, B1...）
                        item_id = f"{batch_letter}{batch_index}"
                        
                        # **关键改进**：使用完整的PLM原始数据来构建metadata
                        metadata = self._flatten_plm_metadata(plm_original_data)
                        
                        # 创建item（imgUrl使用云端URL）
                        item = {
                            "id": item_id,
                            "code": code,
                            "imgUrl": image_url,  # 使用云端presignUrl
                            "metadata": metadata,
                            "batch_id": f"batch_{batch_number}",
                            "batch_index": batch_index
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        continue
                
            except Exception as e:
                continue

        return {"items": items}
    
    def _flatten_plm_metadata(self, plm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将PLM返回的嵌套结构扁平化为单层metadata对象
        
        **改进点**：确保正确处理所有PLM字段，包括嵌套字典和列表
        
        Args:
            plm_data: PLM返回的原始SKU数据
            
        Returns:
            扁平化的metadata对象
        """
        metadata = {}
        
        for key, value in plm_data.items():
            if isinstance(value, dict):
                # 提取description字段（如果存在）- **优先级最高**
                if "description" in value and value["description"]:
                    metadata[key] = value["description"]
                # 提取title字段（如果存在且description不存在）
                elif "title" in value and value["title"]:
                    metadata[key] = value["title"]
                # 提取code字段（如果存在且description不存在）
                elif "code" in value and value["code"]:
                    metadata[key] = value["code"]
                # 如果都没有有效值，保留原始字典（但这种情况很少）
                else:
                    metadata[key] = value
            elif isinstance(value, list):
                # 如果是列表，尝试提取第一个元素的description
                if value and isinstance(value[0], dict):
                    if "description" in value[0] and value[0]["description"]:
                        metadata[key] = value[0]["description"]
                    elif "code" in value[0] and value[0]["code"]:
                        metadata[key] = value[0]["code"]
                    else:
                        metadata[key] = value
                else:
                    metadata[key] = value
            else:
                # 基本类型直接保留
                metadata[key] = value
        
        return metadata

def handler(input_data: Optional[Dict[str, Any]] = None, codes: Optional[List[str]] = None, code: Optional[str] = None, items_info: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    技能入口函数
    
    **关键改进**：正确处理plm-interface的完整输出，确保metadata包含所有PLM字段
    
    Args:
        input_data: 完整输入数据（支持plm-interface输出格式）
        codes: code列表
        code: 单个code
        items_info: 额外信息列表，包含color, category等
    
    Returns:
        处理结果，格式为 {"items": [...]}
    """
    try:
        client = AssetClient()

        # 收集所有code和额外信息
        all_codes = []
        code_info_map = {}

        # 优先处理完整输入数据（plm-interface输出格式）
        if input_data:
            # 解析sku_list
            sku_list = input_data.get("sku_list", [])
            for idx, sku in enumerate(sku_list):
                # **关键改进**：使用codesapr3作为搜索code（完整SAP编码）
                sku_code = sku.get("codesapr3")  # 优先使用codesapr3
                if not sku_code:
                    sku_code = sku.get("code")  # 备用使用code
                
                if sku_code:
                    all_codes.append(sku_code)
                    
                    # **关键改进**：保存完整的原始PLM数据用于metadata构建
                    code_info_map[sku_code] = {
                        "original_plm_data": sku  # 保存完整的SKU对象
                    }
        
        # 处理单独的code参数
        if code:
            all_codes.append(code)
            if code not in code_info_map:
                code_info_map[code] = {"original_plm_data": {}}

        # 处理codes列表
        if codes:
            for code in codes:
                all_codes.append(code)
                if code not in code_info_map:
                    code_info_map[code] = {"original_plm_data": {}}

        # 处理items_info（补充或覆盖信息）
        if items_info:
            for item in items_info:
                item_code = item.get("code")
                if item_code:
                    if item_code not in code_info_map:
                        code_info_map[item_code] = {"original_plm_data": {}}
                    # 合并items_info中的数据到original_plm_data
                    code_info_map[item_code]["original_plm_data"].update(item)

        # 去重（保持顺序）
        seen = set()
        all_codes = [c for c in all_codes if not (c in seen or seen.add(c))]

        if not all_codes:
            return {
                "items": [],
                "message": "未提供任何code"
            }

        # 搜索并下载图片
        return client.search_and_download_v2(all_codes, code_info_map)
        
    except Exception as e:
        return {
            "items": [],
            "message": f"初始化失败: {str(e)}",
            "error": str(e)
        }

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="资产图片获取技能（通过code搜索）")
    parser.add_argument("--code", type=str, required=False,
                        help="单个产品code")
    parser.add_argument("--codes", type=str, required=False,
                        help="JSON格式的code列表")
    parser.add_argument("--check", action="store_true",
                        help="健康检查模式")
    parser.add_argument("--get-folders", action="store_true",
                        help="获取文件夹目录层级")

    args = parser.parse_args()

    try:
        if args.check:
            # 健康检查：验证配置和缓存目录
            client = AssetClient()
            status = {
                "status": "healthy" if client.field_id else "warning",
                "cache_dir": client.cache_dir,
                "base_url": client.base_url,
                "default_folder_id": client.default_folder_id,
                "field_id_configured": bool(client.field_id),
                "sap_field_id_configured": bool(client.sap_field_id),
                "endpoints": client.endpoints,
                "environment_variables": {
                    "ASSETS_API_BASE_URL": os.getenv("ASSETS_API_BASE_URL", "未设置（使用默认值）"),
                    "ASSETS_FIELD_ID": "已设置" if client.field_id else "未设置（必需）",
                    "ASSETS_SAP_FIELD_ID": "已设置" if client.sap_field_id else "未设置（可选）",
                    "ASSETS_FOLDER_ID": os.getenv("ASSETS_FOLDER_ID", "未设置（使用默认值0）")
                }
            }
            if not client.field_id:
                status["message"] = "警告：未配置ASSETS_FIELD_ID环境变量，请联系管理员获取SKU字段的fieldId"
            print(json.dumps(status, ensure_ascii=False))
            sys.exit(0)

        if args.get_folders:
            # 获取文件夹层级
            client = AssetClient()
            folders = client.get_folder_optional()
            print(json.dumps(folders, ensure_ascii=False))
            sys.exit(0)

        # 解析输入参数
        input_data = None
        codes = []
        items_info = None

        if args.code:
            codes.append(args.code)

        if args.codes:
            codes.extend(json.loads(args.codes))

        # 从stdin读取（当没有命令行参数时）
        if not codes:
            input_data_str = sys.stdin.read().strip()
            if input_data_str:
                input_json = json.loads(input_data_str)
                
                # 检查是否是plm-interface输出格式
                if "sku_list" in input_json:
                    input_data = input_json
                else:
                    # 尝试解析其他格式
                    if "codes" in input_json:
                        codes.extend(input_json["codes"])
                    elif "code" in input_json:
                        codes.append(input_json["code"])
                    
                    # 读取额外信息
                    if "items_info" in input_json:
                        items_info = input_json["items_info"]

        # 执行搜索和下载
        if input_data:
            result = handler(input_data=input_data)
        else:
            result = handler(codes=codes, items_info=items_info)

        # 输出结果到stdout
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        # 输出错误到stderr
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()