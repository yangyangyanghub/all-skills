#!/usr/bin/env python3
"""
文生图脚本 (Text-to-Image)
支持 Gemini、DashScope、智谱 API

Author: 翟星人
"""

import httpx
import base64
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Gemini SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
]

# DashScope 尺寸映射
RATIO_TO_SIZE_DASHSCOPE = {
    "1:1": "1328*1328",
    "2:3": "1104*1472",
    "3:2": "1472*1104",
    "3:4": "928*1664",
    "4:3": "1472*1104",
    "4:5": "928*1664",
    "5:4": "1328*1328",
    "9:16": "928*1664",
    "16:9": "1664*928",
    "21:9": "1664*704"
}

# 智谱 GLM-Image 尺寸映射
RATIO_TO_SIZE_ZHIPU = {
    "1:1": "1280x1280",
    "2:3": "1056x1568",
    "3:2": "1568x1056",
    "3:4": "1088x1472",
    "4:3": "1472x1088",
    "9:16": "960x1728",
    "16:9": "1728x960",
    "21:9": "1728x720"
}


class TextToImageGenerator:
    """文生图生成器 - 支持 Gemini、DashScope、智谱 API"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        if config is None:
            config = self._load_config()
        
        self.api_key = config.get('api_key') or config.get('IMAGE_API_KEY')
        self.base_url = config.get('base_url') or config.get('IMAGE_API_BASE_URL')
        self.model = config.get('model') or config.get('IMAGE_MODEL') or 'glm-image'
        
        # 检测 API 类型
        self.is_gemini = 'generativelanguage.googleapis.com' in (self.base_url or '')
        self.is_zhipu = 'bigmodel.cn' in (self.base_url or '')
        self.is_dashscope = 'dashscope.aliyuncs.com' in (self.base_url or '')
        
        if not self.api_key:
            raise ValueError("缺少必要的 API 配置：api_key")
        if not self.is_gemini and not self.base_url:
            raise ValueError("非 Gemini API 需要配置 base_url")
    def _load_config(self) -> Dict[str, str]:
        """从配置文件或环境变量加载配置"""
        config = {}
        
        config_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                api_config = settings.get('image_api', {})
                config['api_key'] = api_config.get('key')
                config['base_url'] = api_config.get('base_url')
                config['model'] = api_config.get('model')
        
        config['api_key'] = os.getenv('IMAGE_API_KEY', config.get('api_key'))
        config['base_url'] = os.getenv('IMAGE_API_BASE_URL', config.get('base_url'))
        config['model'] = os.getenv('IMAGE_MODEL', config.get('model'))
        
        return config
    
    @staticmethod
    def image_to_base64(image_path: str, with_prefix: bool = True) -> str:
        """将图片文件转换为 base64 编码"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        suffix = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(suffix, 'image/png')
        
        with open(image_path, 'rb') as f:
            b64_str = base64.b64encode(f.read()).decode('utf-8')
        
        if with_prefix:
            return f"data:{mime_type};base64,{b64_str}"
        return b64_str
    
    @staticmethod
    def download_image(url: str, output_path: str) -> bool:
        """下载图片到本地"""
        try:
            resp = httpx.get(url, timeout=60)
            resp.raise_for_status()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        output_path: Optional[str] = None,
        negative_prompt: str = "low resolution, low quality, blurry, distorted",
        prompt_extend: bool = False,
        watermark: bool = False
    ) -> Dict[str, Any]:
        """生成图片 - 自动选择 Gemini、智谱或 DashScope API"""
        
        if self.is_gemini:
            return self._generate_gemini(prompt, aspect_ratio, output_path)
        elif self.is_zhipu:
            return self._generate_zhipu(prompt, aspect_ratio, output_path)
        else:
            return self._generate_dashscope(prompt, size, aspect_ratio, output_path, negative_prompt, prompt_extend, watermark)

    def _generate_gemini(
        self,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 Gemini API 生成图片"""
        if not GEMINI_SDK_AVAILABLE:
            return {"success": False, "error": "google-genai SDK 未安装，请运行: pip install google-genai"}

        try:
            client = genai.Client(api_key=self.api_key)
            
            # 默认比例
            ratio = aspect_ratio or "16:9"

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=ratio,
                    ),
                ),
            )

            # 解析响应
            for part in response.parts:
                if part.inline_data:
                    image = part.as_image()
                    if image and output_path:
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        image.save(output_path)
                        return {
                            "success": True,
                            "saved_path": output_path,
                            "image": image
                        }

            return {"success": False, "error": "生成失败：未返回图片数据"}

        except Exception as e:
            return {"success": False, "error": f"Gemini API 错误: {str(e)}"}

    def _generate_zhipu(
        self,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用智谱 API 生成图片 (OpenAI 兼容格式)"""
        
        # 确定尺寸 - 智谱 GLM-Image 推荐尺寸
        final_size = "1280x1280"
        if aspect_ratio:
            final_size = RATIO_TO_SIZE_ZHIPU.get(aspect_ratio, "1280x1280")
        
        # 构建请求 - OpenAI 兼容格式
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": final_size
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # 解析响应 - OpenAI 格式: {"data": [{"url": "..."}]}
                if result.get("data") and len(result["data"]) > 0:
                    image_url = result["data"][0].get("url")
                    
                    if image_url and output_path:
                        if self.download_image(image_url, output_path):
                            return {
                                "success": True,
                                "saved_path": output_path,
                                "image_url": image_url
                            }
                        else:
                            return {
                                "success": True,
                                "image_url": image_url,
                                "saved_path": None
                            }
                    
                    return {
                        "success": True,
                        "image_url": image_url,
                        "saved_path": None
                    }
                
                return {
                    "success": False,
                    "error": "生成失败：未返回图片数据",
                    "detail": result
                }
        
        except httpx.HTTPStatusError as e:
            # 尝试获取错误详情
            try:
                error_detail = e.response.json()
            except:
                error_detail = str(e)
            return {
                "success": False,
                "error": f"HTTP 错误: {e.response.status_code}",
                "detail": error_detail
            }
        except Exception as e:
            return {
                "success": False,
                "error": "生成失败",
                "detail": str(e)
            }

    def _generate_dashscope(
        self,
        prompt: str,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        output_path: Optional[str] = None,
        negative_prompt: str = "",
        prompt_extend: bool = False,
        watermark: bool = False
    ) -> Dict[str, Any]:
        """使用 DashScope API 生成图片"""

        # 确定尺寸
        final_size = "1024*1024"
        if aspect_ratio:
            final_size = RATIO_TO_SIZE_DASHSCOPE.get(aspect_ratio, "1024*1024")
        elif size:
            final_size = size.replace('x', '*')

        # 构建请求 - 使用多模态对话格式
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "size": final_size,
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # 解析响应
                if result.get("output") and result["output"].get("choices"):
                    choices = result["output"]["choices"]
                    if choices and choices[0].get("message"):
                        content = choices[0]["message"].get("content", [])
                        if content and content[0].get("image"):
                            image_url = content[0]["image"]

                            if output_path:
                                # 下载图片
                                if self.download_image(image_url, output_path):
                                    result["saved_path"] = output_path
                                else:
                                    result["image_url"] = image_url

                            return {
                                "success": True,
                                "data": result,
                                "image_url": image_url,
                                "saved_path": output_path if output_path else None
                            }

                return {
                    "success": False,
                    "error": "生成失败",
                    "detail": result
                }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP 错误: {e.response.status_code}",
                "detail": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "生成失败",
                "detail": str(e)
            }
    
    def _save_image(self, b64_data: str, output_path: str) -> None:
        """保存 base64 图片到文件"""
        image_data = base64.b64decode(b64_data)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(image_data)


def main():
    """命令行入口"""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='文生图工具 - 支持 Gemini、智谱、DashScope API')
    parser.add_argument('prompt', help='中文图像描述提示词')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-r', '--ratio', help=f'宽高比，可选: {", ".join(VALID_ASPECT_RATIOS)}')
    parser.add_argument('-s', '--size', help='图片尺寸 (如 1024x1024)')
    parser.add_argument('--no-prompt-extend', action='store_true', help='禁用提示词扩展')
    parser.add_argument('--watermark', action='store_true', help='添加水印')
    
    args = parser.parse_args()
    
    if args.ratio and args.ratio not in VALID_ASPECT_RATIOS:
        print(f"错误: 不支持的宽高比 '{args.ratio}'")
        return
    
    output_path = args.output
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"generated_{timestamp}.png"
    
    generator = TextToImageGenerator()
    result = generator.generate(
        prompt=args.prompt,
        size=args.size,
        aspect_ratio=args.ratio,
        output_path=output_path,
        prompt_extend=not args.no_prompt_extend,
        watermark=args.watermark
    )
    
    if result["success"]:
        print(f"生成成功！")
        if result.get("saved_path"):
            print(f"图片已保存到: {result['saved_path']}")
        elif result.get("image_url"):
            print(f"图片地址: {result['image_url']}")
    else:
        print(f"生成失败: {result['error']}")
        print(f"详情: {result.get('detail', 'N/A')}")


if __name__ == "__main__":
    main()