#!/usr/bin/env python3
"""
GitHub Daily Digest - 每日 GitHub 热门项目报告
获取 GitHub Trending Top 10 + Stars 增长率 Top 10，生成中文总结并发送邮件
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Project:
    """项目数据类"""
    name: str
    url: str
    description: str
    language: str
    stars: int
    forks: int
    stars_today: int = 0
    growth_rate: float = 0.0
    chinese_summary: str = ""

class GitHubTrendingScraper:
    """GitHub Trending 爬虫"""
    
    BASE_URL = "https://github.com/trending"
    
    def get_daily_top10(self, max_retries: int = 3) -> List[Project]:
        """获取今日 Stars 增长 Top 10"""
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试获取 GitHub Trending (第 {attempt + 1} 次)")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(
                    f"{self.BASE_URL}?since=daily",
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                projects = []
                
                # 解析 Trending 页面
                repo_list = soup.select('article.Box-row')
                
                for i, repo in enumerate(repo_list[:10]):
                    try:
                        # 项目名
                        name_elem = repo.select_one('h2 a')
                        name = name_elem.get_text(strip=True).replace('\n', '').replace(' ', '')
                        url = f"https://github.com{name_elem['href']}"
                        
                        # 描述
                        desc_elem = repo.select_one('p')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # 语言
                        lang_elem = repo.select_one('[itemprop="programmingLanguage"]')
                        language = lang_elem.get_text(strip=True) if lang_elem else "N/A"
                        
                        # Stars 和 Forks
                        star_elem = repo.select('a.Link--muted')
                        stars = 0
                        forks = 0
                        
                        if len(star_elem) >= 1:
                            stars_text = star_elem[0].get_text(strip=True).replace(',', '')
                            stars = int(stars_text) if stars_text.isdigit() else 0
                        
                        if len(star_elem) >= 2:
                            forks_text = star_elem[1].get_text(strip=True).replace(',', '')
                            forks = int(forks_text) if forks_text.isdigit() else 0
                        
                        # 今日 Stars
                        today_elem = repo.select_one('span.d-inline-block.float-sm-right')
                        stars_today = 0
                        if today_elem:
                            today_text = today_elem.get_text(strip=True).split()[0].replace(',', '')
                            stars_today = int(today_text) if today_text.isdigit() else 0
                        
                        projects.append(Project(
                            name=name,
                            url=url,
                            description=description,
                            language=language,
                            stars=stars,
                            forks=forks,
                            stars_today=stars_today
                        ))
                        
                    except Exception as e:
                        logger.warning(f"解析第 {i + 1} 个项目失败: {e}")
                        continue
                
                logger.info(f"成功获取 {len(projects)} 个 Trending 项目")
                return projects
                
            except Exception as e:
                logger.error(f"获取 GitHub Trending 失败 (第 {attempt + 1} 次): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 300  # 5分钟, 10分钟, 15分钟
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise

class OssInsightAPI:
    """OssInsight API 客户端"""
    
    BASE_URL = "https://api.ossinsight.io/v1"
    
    def get_rising_stars(self, max_retries: int = 3) -> List[Project]:
        """获取 Stars 增长率最高的项目"""
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试获取 OssInsight 数据 (第 {attempt + 1} 次)")
                
                # 获取最近 24 小时增长最快的项目
                response = requests.get(
                    f"{self.BASE_URL}/trends/repos",
                    params={
                        'period': 'past_24_hours',
                        'limit': 10
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                projects = []
                
                # OssInsight API 返回格式: data.data.rows
                rows = data.get('data', {}).get('rows', [])[:10]
                
                for item in rows:
                    try:
                        repo_name = item.get('repo_name', '')
                        stars = int(item.get('stars', 0)) if item.get('stars') else 0
                        forks = int(item.get('forks', 0)) if item.get('forks') else 0
                        total_score = float(item.get('total_score', 0))
                        
                        # 用 total_score 作为增长指标
                        growth_rate = round(total_score, 2)
                        
                        projects.append(Project(
                            name=repo_name,
                            url=f"https://github.com/{repo_name}",
                            description=item.get('description', ''),
                            language=item.get('primary_language', 'N/A'),
                            stars=stars,
                            forks=forks,
                            stars_today=0,
                            growth_rate=growth_rate
                        ))
                    except Exception as e:
                        logger.warning(f"解析项目失败: {e}")
                        continue
                
                logger.info(f"成功获取 {len(projects)} 个增长最快的项目")
                return projects
                
            except Exception as e:
                logger.error(f"获取 OssInsight 数据失败 (第 {attempt + 1} 次): {e}")
                # 500 错误或其他严重错误，直接用备选方案
                logger.warning("OssInsight API 不可用，使用 GitHub API 备选方案")
                return self._get_fallback_rising_stars()
    
    def _get_fallback_rising_stars(self) -> List[Project]:
        """备选方案：使用 GitHub API 获取最近创建的高 Stars 项目"""
        try:
            # 搜索最近 7 天创建的高 Stars 项目
            date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    'q': f'created:>{date_from} stars:>100',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 10
                },
                headers={
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'GitHub-Daily-Digest'
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            projects = []
            
            for item in data.get('items', []):
                projects.append(Project(
                    name=item['full_name'],
                    url=item['html_url'],
                    description=item.get('description', ''),
                    language=item.get('language', 'N/A'),
                    stars=item['stargazers_count'],
                    forks=item['forks_count'],
                    stars_today=0,
                    growth_rate=0.0
                ))
            
            return projects
            
        except Exception as e:
            logger.error(f"备选方案也失败: {e}")
            return []

class SummaryGenerator:
    """中文总结生成器"""
    
    def __init__(self):
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source='en', target='zh-CN')
            self.has_translator = True
        except ImportError:
            self.has_translator = False
            logger.warning("deep-translator 未安装，将使用简单翻译")
    
    def generate_summary(self, project: Project) -> str:
        """生成中文总结（混合风格：通俗 + 技术细节）"""
        desc = project.description or "暂无描述"
        
        # 翻译描述
        chinese_desc = self._translate(desc)
        
        # 解析技术关键词
        tech_keywords = self._extract_tech_keywords(desc, project.language)
        
        # 生成技术细节
        tech_details = self._generate_tech_details(tech_keywords, project.language)
        
        # 组合
        if tech_details:
            return f"{chinese_desc}\n\n技术栈: {tech_details}"
        else:
            return chinese_desc
    
    def _translate(self, text: str) -> str:
        """翻译英文到中文"""
        if not text or not text.strip():
            return "暂无描述"
        
        if self.has_translator:
            try:
                # 截断过长的文本
                if len(text) > 500:
                    text = text[:500]
                result = self.translator.translate(text)
                return result if result else text
            except Exception as e:
                logger.warning(f"翻译失败: {e}")
                return text
        else:
            return text
    
    def _extract_tech_keywords(self, description: str, language: str) -> List[str]:
        """提取技术关键词"""
        keywords = []
        
        # 常见技术关键词
        tech_terms = [
            'AI', 'ML', 'LLM', 'GPT', 'API', 'CLI', 'SDK', 'DB', 'SQL',
            'REST', 'GraphQL', 'Docker', 'Kubernetes', 'k8s', 'React', 'Vue',
            'Angular', 'Node', 'Python', 'Go', 'Rust', 'Java', 'TypeScript',
            'JavaScript', 'Web', 'Mobile', 'iOS', 'Android', 'Linux', 'Windows',
            'Machine Learning', 'Deep Learning', 'Neural', 'Transformer',
            'Database', 'Cache', 'Queue', 'Stream', 'Real-time', 'Async',
            'Microservice', 'Serverless', 'Cloud', 'AWS', 'Azure', 'GCP'
        ]
        
        desc_lower = description.lower()
        for term in tech_terms:
            if term.lower() in desc_lower:
                keywords.append(term)
        
        # 添加语言
        if language and language != 'N/A':
            keywords.append(language)
        
        return list(set(keywords))[:5]  # 最多5个关键词
    
    def _generate_tech_details(self, keywords: List[str], language: str) -> str:
        """生成技术细节"""
        if not keywords:
            return ""
        
        return "、".join(keywords)

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.use_ssl = os.getenv('SMTP_SSL', 'true').lower() == 'true'
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.recipient_emails = [e.strip() for e in os.getenv('RECIPIENT_EMAIL', '').split(',') if e.strip()]
    
    def send_email(self, subject: str, html_content: str, max_retries: int = 3) -> bool:
        """发送 HTML 邮件"""
        import smtplib
        from email.mime.text import MIMEText
        
        if not self.sender_email or not self.sender_password:
            logger.error("未配置发件人邮箱或密码")
            return False
        
        if not self.recipient_emails:
            logger.error("未配置收件人邮箱")
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试发送邮件 (第 {attempt + 1} 次)")
                
                # 创建邮件
                msg = MIMEText(html_content, 'html', 'utf-8')
                msg['Subject'] = subject
                msg['From'] = self.sender_email
                msg['To'] = ', '.join(self.recipient_emails)
                
                # 发送
                if self.use_ssl:
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                        server.login(self.sender_email, self.sender_password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls()
                        server.login(self.sender_email, self.sender_password)
                        server.send_message(msg)
                
                logger.info("邮件发送成功")
                return True
                
            except Exception as e:
                logger.error(f"发送邮件失败 (第 {attempt + 1} 次): {e}")
                if attempt < max_retries - 1:
                    time.sleep(60)
                else:
                    return False
        
        return False

class DailyDigestGenerator:
    """每日报告生成器"""
    
    def __init__(self):
        self.trending_scraper = GitHubTrendingScraper()
        self.ossinsight_api = OssInsightAPI()
        self.summary_generator = SummaryGenerator()
        self.email_sender = EmailSender()
    
    def generate_report(self) -> Optional[str]:
        """生成完整报告"""
        try:
            # 1. 获取 Trending Top 10
            logger.info("开始获取 GitHub Trending Top 10...")
            trending_projects = self.trending_scraper.get_daily_top10()
            
            # 2. 获取增长最快的 Top 10
            logger.info("开始获取 Stars 增长率 Top 10...")
            rising_projects = self.ossinsight_api.get_rising_stars()
            
            # 3. 生成中文总结
            logger.info("生成中文总结...")
            for project in trending_projects + rising_projects:
                project.chinese_summary = self.summary_generator.generate_summary(project)
            
            # 4. 生成 HTML 报告
            logger.info("生成 HTML 报告...")
            html_report = self._generate_html_report(trending_projects, rising_projects)
            
            return html_report
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return None
    
    def _generate_html_report(self, trending: List[Project], rising: List[Project]) -> str:
        """生成 HTML 报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Trending 表格
        trending_rows = ""
        for i, p in enumerate(trending, 1):
            trending_rows += f"""
            <tr>
                <td>{i}</td>
                <td><a href="{p.url}" target="_blank">{p.name}</a></td>
                <td>{p.chinese_summary}</td>
                <td>{p.language}</td>
                <td>⭐ {p.stars:,}</td>
                <td>+{p.stars_today:,}</td>
            </tr>
            """
        
        # Rising 表格
        rising_rows = ""
        for i, p in enumerate(rising, 1):
            rising_rows += f"""
            <tr>
                <td>{i}</td>
                <td><a href="{p.url}" target="_blank">{p.name}</a></td>
                <td>{p.chinese_summary}</td>
                <td>{p.language}</td>
                <td>⭐ {p.stars:,}</td>
                <td>{p.growth_rate}%</td>
            </tr>
            """
        
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;">
<h2>GitHub 每日精华 - {today}</h2>

<h3>Stars 昨日增长 Top 10</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
<tr><th>#</th><th>项目</th><th>简介</th><th>语言</th><th>Stars</th><th>增长</th></tr>
{trending_rows}
</table>

<h3>Stars 增长率 Top 10</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
<tr><th>#</th><th>项目</th><th>简介</th><th>语言</th><th>Stars</th><th>增长率</th></tr>
{rising_rows}
</table>

<p style="color:#666;font-size:12px;margin-top:30px;">数据来源: GitHub Trending + OssInsight API | 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</body>
</html>"""
        
        return html
    
    def run(self) -> bool:
        """运行完整流程"""
        logger.info("开始生成 GitHub 每日精华报告...")
        
        # 生成报告
        html_report = self.generate_report()
        
        if not html_report:
            logger.error("报告生成失败")
            return False
        
        # 发送邮件
        today = datetime.now().strftime('%Y-%m-%d')
        subject = f"GitHub Daily Digest - {today}"
        
        success = self.email_sender.send_email(subject, html_report)
        
        if success:
            logger.info("报告发送成功!")
        else:
            logger.error("报告发送失败")
        
        return success

def main():
    """主函数"""
    generator = DailyDigestGenerator()
    success = generator.run()
    
    if not success:
        sys.exit(1)
    
    logger.info("GitHub 每日精华报告生成完成")

if __name__ == '__main__':
    main()
