import os
import json
import time
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as mc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from datetime import datetime, timedelta

data_path = "data/astrbot_plugin_uptime.json"

@register("astrbot_plugin_uptime", "Soulter", "监测站点，异常时发出警报", "1.0.0", "https://github.com/Soulter/astrbot_plugin_uptime")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.interval = config.get("interval", 3)
        self.scheduler = AsyncIOScheduler()
        
        if not os.path.exists(data_path):
            with open(data_path, "w") as f:
                json.dump({}, f)
        with open(data_path, "r") as f:
            self.data = json.load(f)
        self.last_normal_time = {}
        self.error_flags = {}
        self.last_response_time = {}

    async def initialize(self):
        self.scheduler.add_job(self.check_sites, 'interval', minutes=self.interval, misfire_grace_time=60)
        self.scheduler.start()

    def human_readable_time_diff(self, past_time):
        now = datetime.now()
        diff = now - past_time
        days, seconds = diff.days, diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{days}天 {hours}小时 {minutes}分钟"

    async def check_site(self, session, user, site):
        try:
            start_time = datetime.now()
            async with session.get(site) as response:
                response_time = datetime.now() - start_time
                self.last_response_time[site] = response_time.total_seconds()
                if response.status == 200:
                    self.last_normal_time[site] = datetime.now()
                    if site in self.error_flags and self.error_flags[site]:
                        self.error_flags[site] = False
                else:
                    await self.handle_site_error(user, site, f"响应异常，状态码: {response.status}")
        except Exception as e:
            await self.handle_site_error(user, site, f"检测失败，错误: {str(e)}")

    async def handle_site_error(self, user, site, error_message):
        if site not in self.error_flags or not self.error_flags[site]:
            
            plain = (
                f"⚠ 站点异常 {site}\n"
                f"网站: {site}\n"
                f"错误信息: {error_message}"
            )
            
            await self.context.send_message(user, MessageChain(chain=[
                mc.Plain(plain)
            ]))
            self.error_flags[site] = True

    async def check_sites(self):
        async with aiohttp.ClientSession() as session:
            for user, sites in self.data.items():
                for site in sites:
                    await self.check_site(session, user, site)

    @filter.command_group("uptime")
    def uptime(self):
        pass
    
    @uptime.command("add")
    async def add_uptime(self, event: AstrMessageEvent, url: str):
        '''添加一个站点链接'''
        userid = event.unified_msg_origin
        url = url.strip()
        if userid not in self.data:
            self.data[userid] = []
        if url not in self.data[userid]:
            self.data[userid].append(url)
            self.last_normal_time[url] = datetime.now()
            self.error_flags[url] = False
            with open(data_path, "w") as f:
                json.dump(self.data, f)
            yield event.plain_result(f"✅ 站点 {url} 已添加到监控列表。")
        else:
            yield event.plain_result(f"ℹ️ 站点 {url} 已存在于监控列表中。")

    @uptime.command("ls")
    async def list_uptime(self, event: AstrMessageEvent):
        '''列出所有监控的站点'''
        userid = event.unified_msg_origin
        if userid in self.data and self.data[userid]:
            sites_list = "\n".join(self.data[userid])
            yield event.plain_result(f"📋 当前监控的站点:\n{sites_list}")
        else:
            yield event.plain_result("ℹ️ 当前没有监控的站点。")

    @uptime.command("del")
    async def delete_uptime(self, event: AstrMessageEvent, url: str):
        '''删除一个监控的站点'''
        userid = event.unified_msg_origin
        url = url.strip()
        if userid in self.data and url in self.data[userid]:
            self.data[userid].remove(url)
            if url in self.last_normal_time:
                del self.last_normal_time[url]
            if url in self.error_flags:
                del self.error_flags[url]
            with open(data_path, "w") as f:
                json.dump(self.data, f)
            yield event.plain_result(f"✅ 站点 {url} 已从监控列表中删除。")
        else:
            yield event.plain_result(f"ℹ️ 站点 {url} 不存在于监控列表中。")

    @uptime.command("status")
    async def status_uptime(self, event: AstrMessageEvent):
        '''检查所有站点的当前状态'''
        userid = event.unified_msg_origin
        if userid in self.data and self.data[userid]:
            status_list = []
            async with aiohttp.ClientSession() as session:
                for site in self.data[userid]:
                    status_list.append(await self.get_site_status(session, site))
            status_message = "\n\n".join(status_list)
            yield event.plain_result(f"📋 站点状态:\n{status_message}")
        else:
            yield event.plain_result("ℹ️ 当前没有监控的站点。")

    async def get_site_status(self, session, site):
        try:
            start_time = time.time()
            async with session.get(site) as response:
                response_time = (time.time() - start_time)*1000
                delay = f"{response_time:.2f} ms"
                if response.status == 200:
                    if site in self.last_normal_time:
                        last_normal_time = self.last_normal_time[site]
                        time_diff = self.human_readable_time_diff(last_normal_time)
                        return f"✅ {site} 正常 {delay}\n🕒 持续: {time_diff}"
                    else:
                        return f"✅ {site} 正常 {delay}"
                else:
                    return f"❌ {site} 异常 {delay} {response.status}"
                    
        except Exception as e:
            return f"❌ {site} 检测失败: {str(e)}"
