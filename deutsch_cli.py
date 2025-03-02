#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
德语学习助手 - 命令行工具
为德语初学者(A1级别)提供翻译、语法分析、拼写纠错和发音指导等功能.
"""

import os
import sys
import json
import time
import tempfile
from typing import List, Dict, Any, Tuple, Optional, Union
import logging
import re
from pathlib import Path
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import spacy
try:
    import de_core_news_sm
except ImportError:
    os.system('python -m spacy download de_core_news_sm')
    import de_core_news_sm
try:
    import language_tool_python
    LANGUAGE_TOOL_AVAILABLE = True
except (ImportError, OSError):
    LANGUAGE_TOOL_AVAILABLE = False
from gtts import gTTS
from pydub import AudioSegment
try:
    import simpleaudio as sa
except ImportError:
    # 如果simpleaudio不可用,则尝试使用系统命令播放
    sa = None
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from colorama import Fore, Style, init as colorama_init
import hashlib
import platform
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("deutsch_helper.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 初始化colorama
colorama_init(autoreset=True)

# 加载环境变量
load_dotenv()

# 平台检测
IS_MAC = sys.platform == 'darwin'


class Translator:
    """翻译器类,提供德语和中文之间的相互翻译功能."""
    
    def __init__(self):
        """初始化翻译器"""
        self.de_to_zh = GoogleTranslator(source='de', target='zh-CN')
        self.zh_to_de = GoogleTranslator(source='zh-CN', target='de')
        logger.info("翻译器初始化完成")
    
    def translate(self, text: str, to_lang: str = 'zh-CN') -> str:
        """
        翻译文本
        
        Args:
            text: 需要翻译的文本
            to_lang: 目标语言,默认为中文('zh-CN')
            
        Returns:
            翻译后的文本
        """
        try:
            # 自动检测语言方向
            if any(ord(char) > 127 for char in text):  # 如果包含中文字符
                result = self.zh_to_de.translate(text)
                logger.info(f"将中文翻译为德语: {text} -> {result}")
            else:  # 否则视为德语
                result = self.de_to_zh.translate(text)
                logger.info(f"将德语翻译为中文: {text} -> {result}")
            
            return result
        except Exception as e:
            logger.error(f"翻译出错: {str(e)}")
            return f"翻译错误: {str(e)}"
    
    def translate_with_explanation(self, text: str) -> Dict[str, str]:
        """
        翻译文本并提供更详细的解释
        
        Args:
            text: 需要翻译的文本
            
        Returns:
            包含翻译和解释的字典
        """
        translation = self.translate(text)
        
        # 为德语单词提供额外解释
        explanation = ""
        if not any(ord(char) > 127 for char in text):  # 如果是德语文本
            # 尝试为德语单词添加解释
            words = text.split()
            if len(words) <= 5:  # 对短句或单词提供更详细解释
                for word in words:
                    try:
                        word_explanation = self.get_word_explanation(word)
                        if word_explanation:
                            explanation += f"{word}: {word_explanation}\n"
                    except Exception as e:
                        logger.error(f"获取单词解释失败: {str(e)}")
        
        return {
            "translation": translation,
            "explanation": explanation.strip()
        }
    
    def get_word_explanation(self, word: str) -> str:
        """获取德语单词的详细解释"""
        # 这里可以集成词典API实现更详细的解释
        # 简化版本,仅作示例
        try:
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/de/{word.lower()}"
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    meanings = []
                    for meaning in data[0].get("meanings", []):
                        part_of_speech = meaning.get("partOfSpeech", "")
                        definitions = []
                        for definition in meaning.get("definitions", [])[:2]:
                            definitions.append(definition.get("definition", ""))
                        
                        if part_of_speech and definitions:
                            meanings.append(f"{part_of_speech}: {'; '.join(definitions)}")
                    
                    return " | ".join(meanings[:2])
            return ""
        except Exception as e:
            logger.error(f"词典查询错误: {str(e)}")
            return ""


class Analyzer:
    """语法分析器类,提供德语句子的词性和语法结构分析."""
    
    def __init__(self):
        """初始化语法分析器"""
        self.nlp = de_core_news_sm.load()
        
        # 德语词性映射表(为中文用户提供更友好的解释)
        self.pos_mapping = {
            "ADJ": "形容词",
            "ADP": "介词",
            "ADV": "副词",
            "AUX": "助动词",
            "CCONJ": "并列连词",
            "DET": "限定词",
            "INTJ": "感叹词",
            "NOUN": "名词",
            "NUM": "数词",
            "PART": "虚词",
            "PRON": "代词",
            "PROPN": "专有名词",
            "PUNCT": "标点符号",
            "SCONJ": "从属连词",
            "SYM": "符号",
            "VERB": "动词",
            "X": "其他"
        }
        
        # 德语格的映射表
        self.case_mapping = {
            "Nom": "主格",
            "Gen": "属格",
            "Dat": "与格",
            "Acc": "宾格"
        }
        
        # 德语时态映射表
        self.tense_mapping = {
            "Pres": "现在时",
            "Past": "过去时",
            "Perf": "完成时",
            "Fut": "将来时"
        }
        
        # 德语数的映射表
        self.number_mapping = {
            "Sing": "单数",
            "Plur": "复数"
        }
        
        # 德语性别映射表
        self.gender_mapping = {
            "Masc": "阳性",
            "Fem": "阴性",
            "Neut": "中性"
        }
        
        # 德语人称映射表
        self.person_mapping = {
            "1": "第一人称",
            "2": "第二人称",
            "3": "第三人称"
        }
        
        logger.info("语法分析器初始化完成")
    
    def analyze(self, text: str) -> List[Dict[str, str]]:
        """
        分析德语句子的语法结构和词性
        
        Args:
            text: 需要分析的德语句子
            
        Returns:
            包含每个单词详细分析的列表
        """
        try:
            doc = self.nlp(text)
            results = []
            
            for token in doc:
                word_info = {
                    "word": token.text,
                    "lemma": token.lemma_,  # 词根
                    "pos": f"{token.pos_} ({self.pos_mapping.get(token.pos_, '未知')})",
                    "tag": token.tag_,  # 详细标签
                    "dep": token.dep_,  # 依存关系
                    "explanation": self._get_word_explanation(token)
                }
                results.append(word_info)
            
            # 添加整个句子的时态分析
            sentence_tense = self._analyze_sentence_tense(doc)
            
            return results
        except Exception as e:
            logger.error(f"语法分析出错: {str(e)}")
            return [{"word": text, "error": f"分析错误: {str(e)}"}]
    
    def _get_word_explanation(self, token) -> str:
        """根据词性生成解释"""
        explanation = []
        
        # 根据词性添加不同的解释
        if token.pos_ == "NOUN":
            gender = ""
            for morph in token.morph:
                if morph[0] == "Gender":
                    gender = self.gender_mapping.get(morph[1], "")
            
            case = ""
            for morph in token.morph:
                if morph[0] == "Case":
                    case = self.case_mapping.get(morph[1], "")
            
            if gender:
                explanation.append(f"{gender}名词")
            if case:
                explanation.append(f"{case}")
        
        elif token.pos_ == "VERB":
            tense = ""
            for morph in token.morph:
                if morph[0] == "Tense":
                    tense = self.tense_mapping.get(morph[1], "")
            
            person = ""
            for morph in token.morph:
                if morph[0] == "Person":
                    person = self.person_mapping.get(morph[1], "")
            
            number = ""
            for morph in token.morph:
                if morph[0] == "Number":
                    number = self.number_mapping.get(morph[1], "")
            
            if tense:
                explanation.append(f"{tense}")
            if person and number:
                explanation.append(f"{person}{number}")
        
        elif token.pos_ == "PRON":
            case = ""
            for morph in token.morph:
                if morph[0] == "Case":
                    case = self.case_mapping.get(morph[1], "")
            
            if case:
                explanation.append(f"{case}")
        
        elif token.pos_ == "ADJ":
            case = ""
            for morph in token.morph:
                if morph[0] == "Case":
                    case = self.case_mapping.get(morph[1], "")
            
            if case:
                explanation.append(f"{case}")
            
            if "Degree=Comp" in str(token.morph):
                explanation.append("比较级")
            elif "Degree=Sup" in str(token.morph):
                explanation.append("最高级")
            
        return ",".join(explanation)
    
    def _analyze_sentence_tense(self, doc) -> str:
        """分析整个句子的时态"""
        # 基本时态检测逻辑
        has_aux = False
        has_past_participle = False
        has_present = False
        has_past = False
        
        for token in doc:
            if token.pos_ == "AUX":
                has_aux = True
                if "Tense=Past" in str(token.morph):
                    has_past = True
                elif "Tense=Pres" in str(token.morph):
                    has_present = True
            
            if token.pos_ == "VERB" and "VerbForm=Part" in str(token.morph):
                has_past_participle = True
                
            if token.pos_ == "VERB" and "Tense=Past" in str(token.morph):
                has_past = True
                
        if has_aux and has_past_participle and has_present:
            return "现在完成时 (Perfekt)"
        elif has_aux and has_past_participle and has_past:
            return "过去完成时 (Plusquamperfekt)"
        elif has_past:
            return "过去时 (Präteritum)"
        elif "werden" in [token.lemma_ for token in doc] and any(token.pos_ == "VERB" for token in doc):
            return "将来时 (Futur)"
        else:
            return "现在时 (Präsens)"
    
    def format_analysis(self, analysis_results: List[Dict[str, str]]) -> str:
        """美化格式化分析结果"""
        formatted = ""
        for item in analysis_results:
            formatted += f"• {item['word']}:{item['pos']}"
            if item['explanation']:
                formatted += f",{item['explanation']}"
            if item['lemma'] != item['word']:
                formatted += f",词根:{item['lemma']}"
            formatted += "\n"
        
        return formatted


class Corrector:
    """拼写和语法纠错器类,用于检测和纠正德语句子中的错误."""
    
    def __init__(self):
        """初始化纠错器"""
        self.tool = None
        if LANGUAGE_TOOL_AVAILABLE:
            try:
                self.tool = language_tool_python.LanguageTool('de-DE')
                logger.info("拼写和语法纠错器初始化完成")
            except Exception as e:
                logger.error(f"无法初始化LanguageTool: {str(e)}")
                self.tool = None
        else:
            logger.warning("LanguageTool未安装或Java环境不可用,纠错功能将使用备用方案")
    
    def is_available(self) -> bool:
        """检查纠错器是否可用"""
        return self.tool is not None
    
    def correct(self, text: str) -> Dict[str, Any]:
        """
        检查并纠正德语文本中的拼写和语法错误
        
        Args:
            text: 需要检查的德语文本
            
        Returns:
            包含原文本、纠正后文本和错误详情的字典
        """
        # 如果LanguageTool不可用,使用简单的拼写检查逻辑
        if not self.is_available():
            return self._simple_correction(text)
            
        try:
            matches = self.tool.check(text)
            
            corrected_text = language_tool_python.utils.correct(text, matches)
            
            # 收集错误详情
            errors = []
            for match in matches:
                error_info = {
                    "message": match.message,
                    "context": match.context,
                    "offset": match.offset,
                    "length": match.errorLength,
                    "category": match.category,
                    "rule_id": match.ruleId,
                    "replacements": match.replacements[:3]  # 仅展示前三个替换建议
                }
                errors.append(error_info)
            
            return {
                "original": text,
                "corrected": corrected_text,
                "has_changes": text != corrected_text,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"纠错出错: {str(e)}")
            return self._simple_correction(text)
    
    def _simple_correction(self, text: str) -> Dict[str, Any]:
        """简单的拼写检查逻辑,用于LanguageTool不可用时"""
        # 德语常见错误替换规则
        replacements = {
            # 常见拼写错误
            'ss': 'ß',  # 在某些情况下ss应该是ß
            'ae': 'ä',  # 简化写法替换
            'oe': 'ö',  # 简化写法替换
            'ue': 'ü',  # 简化写法替换
            
            # 常见语法错误 - 这只是示例,实际使用需要更复杂的规则
            'ein der': 'ein',  # 冠词错误修正
            'ein die': 'eine',
            'ein das': 'ein',
            'eine der': 'ein',
            'eine das': 'ein',
        }
        
        # 执行简单替换
        corrected = text
        errors = []
        
        # 检查常见错误
        for error, correction in replacements.items():
            if error in text.lower():
                # 只作为建议,不自动替换
                errors.append({
                    "message": f"可能需要将'{error}'改为'{correction}'",
                    "replacements": [correction]
                })
        
        # 检查句子首字母大写
        if text and text[0].islower() and len(text) > 1:
            errors.append({
                "message": "德语句子首字母应该大写",
                "replacements": [text[0].upper() + text[1:]]
            })
        
        # 检查结尾标点
        if text and not text.endswith(('.', '!', '?')):
            errors.append({
                "message": "句子结尾应该有标点符号",
                "replacements": [text + '.']
            })
        
        return {
            "original": text,
            "corrected": text,  # 保持原样,只提供建议
            "has_changes": len(errors) > 0,
            "errors": errors,
            "limited_mode": True  # 表示这是有限功能模式
        }
    
    def format_corrections(self, correction_result: Dict[str, Any]) -> str:
        """格式化纠正结果,使其更易于理解"""
        if not correction_result["has_changes"]:
            return "没有发现错误,文本正确!"
        
        if correction_result.get("limited_mode", False):
            formatted = "注意: 完整的语法检查功能不可用 (需要Java环境).\n以下是基于简单规则的建议:\n\n"
        else:
            formatted = f"纠正后的文本: {correction_result['corrected']}\n\n错误详情:\n"
        
        for i, error in enumerate(correction_result["errors"], 1):
            formatted += f"{i}. {error['message']}\n"
            if error.get("replacements"):
                formatted += f"   建议修改: {', '.join(error['replacements'])}\n"
            formatted += "\n"
        
        return formatted


class PronunciationGuide:
    """发音指导类,提供德语单词和句子的发音指导."""
    
    def __init__(self, api_key=None):
        self.tts = gTTS
        self.logger = logging.getLogger(__name__)
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger.info(f"初始化发音指导,临时音频目录: {self.temp_dir}")
        
    def get_pronunciation(self, word):
        """获取德语单词的发音指导和音频"""
        try:
            # 生成音频文件
            audio_file = self._generate_audio(word)
            
            # 分析发音
            pronunciation_guide = self.analyze_pronunciation(word)
            
            return {
                'audio_file': audio_file,
                'guide': pronunciation_guide
            }
        except Exception as e:
            self.logger.error(f"获取发音时出错: {str(e)}")
            return {
                'audio_file': None,
                'guide': f"无法获取发音指导: {str(e)}"
            }
    
    def _generate_audio(self, text):
        """生成德语文本的音频文件"""
        try:
            # 创建唯一的文件名
            filename = f"pronunciation_{hashlib.md5(text.encode()).hexdigest()}.mp3"
            filepath = os.path.join(self.temp_dir, filename)
            
            # 如果文件已存在,直接返回
            if os.path.exists(filepath):
                self.logger.info(f"音频文件已存在: {filepath}")
                return filepath
            
            # 生成新的音频文件
            tts = self.tts(text=text, lang='de', slow=False)
            tts.save(filepath)
            self.logger.info(f"生成音频文件: {filepath}")
            
            return filepath
        except Exception as e:
            self.logger.error(f"生成音频文件时出错: {str(e)}")
            return None
    
    def analyze_pronunciation(self, text):
        """分析德语文本中的发音难点"""
        pronunciation_tips = []
        
        # 检查常见的德语发音难点
        if 'ei' in text:
            pronunciation_tips.append("'ei' 发音: [aɪ̯] - 双元音,类似汉语\"爱\"的音")
        
        if 'ie' in text:
            pronunciation_tips.append("'ie' 发音: [iː] - 长元音,发长\"i\"的音")
        
        if 'eu' in text or 'äu' in text:
            pronunciation_tips.append("'eu' 发音: [ɔʏ̯] - 双元音,类似汉语\"欧伊\"连读的音")
        
        if 'ch' in text:
            pronunciation_tips.append("'ch' 发音: 在i,e,ä,ö,ü后发 [ç] (像汉语\"希\"的音); 在a,o,u后发 [x] (像汉语\"喝\"的音)")
        
        if 'sch' in text:
            pronunciation_tips.append("'sch' 发音: [ʃ] - 清擦音,类似汉语\"诗\"的声母")
        
        if 'w' in text:
            pronunciation_tips.append("'w' 发音: [v] - 浊擦音,发\"v\"的音")
        
        if 'v' in text:
            pronunciation_tips.append("'v' 发音: 大多数情况下发 [f],某些外来词中发 [v]")
        
        if 'z' in text:
            pronunciation_tips.append("'z' 发音: [ts] - 清塞擦音,类似汉语\"资\"的声母")
        
        if 'r' in text:
            pronunciation_tips.append("'r' 发音: [ʁ] - 浊擦音,发自喉咙的\"r\"音")
        
        if 'ß' in text:
            pronunciation_tips.append("'ß' 发音: [s] - 清擦音,发\"s\"的音")
        
        if 'ü' in text:
            pronunciation_tips.append("'ü' 发音: [y] - 圆唇前高元音,嘴型发\"i\"但嘴唇圆")
        
        if 'ö' in text:
            pronunciation_tips.append("'ö' 发音: [ø] - 圆唇前中元音,嘴型发\"e\"但嘴唇圆")
        
        if 'ä' in text:
            pronunciation_tips.append("'ä' 发音: [ɛ] - 前中低元音,类似汉语\"哎\"的音")
        
        # 如果没有找到特殊发音点,返回一般提示
        if not pronunciation_tips:
            pronunciation_tips.append("没有发现特殊发音难点,请注意德语的重音通常在第一个音节.")
        
        return pronunciation_tips

    def play_pronunciation(self, audio_file):
        """播放发音音频文件"""
        if not audio_file or not os.path.exists(audio_file):
            self.logger.error(f"音频文件不存在: {audio_file}")
            print("无法播放音频:文件不存在")
            return False
        
        try:
            # 根据操作系统选择播放方法
            platform_name = platform.system().lower()
            
            # 尝试使用系统命令播放
            success = self._play_with_system_command(audio_file, platform_name)
            if success:
                return True
                
            # 如果系统命令失败,尝试使用pydub和simpleaudio
            if audio_file.endswith('.mp3'):
                try:
                    self.logger.info("尝试使用pydub和simpleaudio播放音频")
                    # 将MP3转换为WAV(simpleaudio不支持MP3)
                    sound = AudioSegment.from_mp3(audio_file)
                    wav_file = audio_file.replace('.mp3', '.wav')
                    sound.export(wav_file, format="wav")
                    
                    # 使用simpleaudio播放WAV文件
                    wave_obj = sa.WaveObject.from_wave_file(wav_file)
                    play_obj = wave_obj.play()
                    play_obj.wait_done()  # 等待播放完成
                    
                    # 清理临时WAV文件
                    try:
                        os.remove(wav_file)
                    except Exception as e:
                        self.logger.warning(f"清理临时WAV文件时出错: {str(e)}")
                    
                    return True
                except Exception as e:
                    self.logger.error(f"使用pydub和simpleaudio播放音频时出错: {str(e)}")
            
            # 所有方法都失败
            print("无法播放音频,请确保您的系统支持音频播放")
            return False
            
        except Exception as e:
            self.logger.error(f"播放音频时出错: {str(e)}")
            print(f"播放音频时出错: {str(e)}")
            return False
    
    def _play_with_system_command(self, audio_file, platform_name):
        """使用系统命令播放音频"""
        try:
            command = None
            
            if platform_name == 'darwin':  # macOS
                command = ['afplay', audio_file]
            elif platform_name == 'windows':
                command = ['start', audio_file]
            elif platform_name == 'linux':
                # 尝试多种Linux播放器
                players = ['aplay', 'paplay', 'mplayer', 'mpg123', 'mpg321']
                for player in players:
                    try:
                        subprocess.run(['which', player], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        command = [player, audio_file]
                        break
                    except subprocess.CalledProcessError:
                        continue
            
            if command:
                self.logger.info(f"使用系统命令播放音频: {' '.join(command)}")
                subprocess.run(command, check=False)
                return True
            else:
                self.logger.warning(f"未找到适用于{platform_name}的音频播放命令")
                return False
                
        except Exception as e:
            self.logger.error(f"使用系统命令播放音频时出错: {str(e)}")
            return False


class DeutschCLI:
    """德语学习助手命令行界面类"""
    
    def __init__(self):
        """初始化命令行界面"""
        self.translator = Translator()
        self.analyzer = Analyzer()
        self.corrector = Corrector()
        self.pronunciation_guide = PronunciationGuide()
        self.console = Console()
        
        # 使用rich库美化界面
        self.rich_styles = {
            "title": "bold cyan",
            "subtitle": "bold green",
            "error": "bold red",
            "success": "bold green",
            "warning": "bold yellow",
            "info": "bold blue",
            "input": "bold white"
        }
        
        logger.info("德语学习助手CLI界面初始化完成")
    
    def start(self) -> None:
        """启动命令行界面"""
        try:
            self._show_welcome()
            
            while True:
                choice = self._show_menu()
                
                if choice == "1":
                    self._translation_mode()
                elif choice == "2":
                    self._analysis_mode()
                elif choice == "3":
                    self._correction_mode()
                elif choice == "4":
                    self._pronunciation_mode()
                elif choice == "5":
                    self._show_exit_message()
                    break
                else:
                    self.console.print("[bold red]无效选择,请重新输入![/bold red]")
        except KeyboardInterrupt:
            self._show_exit_message()
        except Exception as e:
            logger.error(f"CLI运行出错: {str(e)}")
            self.console.print(f"[bold red]程序出错: {str(e)}[/bold red]")
            self._show_exit_message()
    
    def _show_welcome(self) -> None:
        """显示欢迎信息"""
        title = Text("德语学习助手 (Deutsch Lernhelfer)", style="bold cyan")
        subtitle = Text("专为A1级别德语学习者设计", style="italic green")
        
        panel = Panel(
            Text.assemble(title, "\n", subtitle),
            box=box.ROUNDED,
            expand=False,
            border_style="cyan"
        )
        
        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")
    
    def _show_menu(self) -> str:
        """显示主菜单并获取用户选择"""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("选项", style="cyan")
        table.add_column("功能", style="green")
        
        table.add_row("1", "翻译功能")
        table.add_row("2", "语法分析")
        table.add_row("3", "拼写纠错")
        table.add_row("4", "发音指导")
        table.add_row("5", "退出程序")
        
        self.console.print(table)
        return input("\n请选择功能 (1-5): ")
    
    def _translation_mode(self) -> None:
        """翻译模式"""
        self.console.print("\n[bold cyan]翻译模式[/bold cyan]")
        self.console.print("输入德语文本将翻译成中文,输入中文文本将翻译成德语.")
        self.console.print("输入 'q' 返回主菜单.\n")
        
        while True:
            text = input("请输入要翻译的文本: ")
            if text.lower() == 'q':
                break
                
            if not text.strip():
                self.console.print("[bold yellow]请输入有效文本![/bold yellow]")
                continue
                
            result = self.translator.translate_with_explanation(text)
            
            # 使用rich显示结果
            result_panel = Panel(
                Text.assemble(
                    Text("翻译结果: ", style="bold green"),
                    Text(result["translation"], style="white"),
                    Text("\n\n") if result["explanation"] else Text(""),
                    Text("详细解释: \n", style="bold green") if result["explanation"] else Text(""),
                    Text(result["explanation"], style="white") if result["explanation"] else Text("")
                ),
                box=box.ROUNDED,
                expand=False,
                border_style="green",
                title="翻译结果"
            )
            
            self.console.print(result_panel)
            self.console.print("\n")
    
    def _analysis_mode(self) -> None:
        """语法分析模式"""
        self.console.print("\n[bold cyan]语法分析模式[/bold cyan]")
        self.console.print("分析德语句子的词性、单词成分和时态")
        self.console.print("输入 'q' 返回主菜单.\n")
        
        while True:
            text = input("请输入要分析的德语句子: ")
            if text.lower() == 'q':
                break
                
            if not text.strip():
                self.console.print("[bold yellow]请输入有效文本![/bold yellow]")
                continue
            
            # 分析句子
            analysis_results = self.analyzer.analyze(text)
            
            # 翻译句子帮助理解
            translation = self.translator.translate(text)
            
            # 创建表格展示分析结果
            table = Table(show_header=True, box=box.ROUNDED)
            table.add_column("单词", style="cyan")
            table.add_column("词性", style="green")
            table.add_column("词根", style="blue")
            table.add_column("说明", style="yellow")
            
            for item in analysis_results:
                table.add_row(
                    item["word"],
                    item["pos"],
                    item["lemma"],
                    item["explanation"]
                )
            
            self.console.print(f"\n[bold green]句子翻译:[/bold green] {translation}\n")
            self.console.print(table)
            self.console.print("\n")
    
    def _correction_mode(self) -> None:
        """拼写纠错模式"""
        self.console.print("\n[bold cyan]拼写纠错模式[/bold cyan]")
        
        # 检查纠错器是否可用
        if not self.corrector.is_available():
            self.console.print("[bold yellow]警告: 完整的语法检查功能不可用 (需要Java环境)[/bold yellow]")
            self.console.print("[bold yellow]将使用基本拼写检查功能,功能有限[/bold yellow]")
        
        self.console.print("检查并纠正德语句子中的拼写和语法错误")
        self.console.print("输入 'q' 返回主菜单.\n")
        
        while True:
            text = input("请输入要纠错的德语句子: ")
            if text.lower() == 'q':
                break
                
            if not text.strip():
                self.console.print("[bold yellow]请输入有效文本![/bold yellow]")
                continue
            
            # 纠正文本
            correction_result = self.corrector.correct(text)
            
            if not correction_result["has_changes"]:
                self.console.print("[bold green]恭喜!文本没有错误.[/bold green]\n")
                continue
            
            # 显示原文和纠正后的文本
            self.console.print(f"\n[bold yellow]原始文本:[/bold yellow] {correction_result['original']}")
            
            if not correction_result.get("limited_mode", False):
                self.console.print(f"[bold green]纠正后的文本:[/bold green] {correction_result['corrected']}\n")
            
            # 显示错误详情
            if correction_result["errors"]:
                table = Table(show_header=True, box=box.SIMPLE)
                table.add_column("错误/建议", style="red")
                table.add_column("建议修改", style="green")
                
                for error in correction_result["errors"]:
                    message = error["message"] 
                    replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "无建议"
                    table.add_row(message, replacements)
                
                self.console.print(table)
                self.console.print("\n")
    
    def _pronunciation_mode(self) -> None:
        """发音指导模式"""
        print("\n发音指导模式")
        print("获取德语单词的发音指导和音频")
        print("输入 'q' 返回主菜单.\n")
        
        while True:
            text = input("请输入要查询发音的德语单词: ")
            if text.lower() == 'q':
                break
            
            result = self.pronunciation_guide.get_pronunciation(text)
            
            if result['guide']:
                # 使用rich库创建一个漂亮的表格显示发音指导
                table = Table(title=f"'{text}' 的发音指导", box=box.ROUNDED)
                table.add_column("发音提示", style="cyan")
                
                for tip in result['guide']:
                    table.add_row(tip)
                
                console = Console()
                console.print(table)
            
            if result['audio_file']:
                print("\n正在播放发音...")
                try:
                    success = self.pronunciation_guide.play_pronunciation(result['audio_file'])
                    if not success:
                        print("无法播放音频,请检查您的音频设置")
                except Exception as e:
                    print(f"播放音频时出错: {str(e)}")
            else:
                print("无法生成音频文件")
    
    def _show_exit_message(self) -> None:
        """显示退出信息"""
        self.console.print("\n[bold cyan]感谢使用德语学习助手!Auf Wiedersehen![/bold cyan]\n")


def main():
    """主函数"""
    try:
        cli = DeutschCLI()
        cli.start()
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        print(f"\n{Fore.RED}程序出错: {str(e)}{Style.RESET_ALL}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main()) 