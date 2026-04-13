"""
Telegram Notifier — ส่งแจ้งเตือนการเทรด, sentiment, และ error ภาษาไทย
"""

import httpx
from loguru import logger

from app.config import settings

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

SENTIMENT_TH = {"bullish": "ขาขึ้น", "bearish": "ขาลง", "neutral": "ทรงตัว"}
SYMBOL_TH = {
    "GOLD": "ทองคำ", "OILCash": "น้ำมัน WTI",
    "BTCUSD": "Bitcoin", "USDJPY": "USD/JPY",
}


class TelegramNotifier:
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(self.token and self.chat_id)

    async def _send(self, text: str):
        if not self.enabled:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    TELEGRAM_API.format(token=self.token),
                    json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                )
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

    def _sym(self, symbol: str) -> str:
        return SYMBOL_TH.get(symbol, symbol)

    async def send_trade_alert(
        self, trade_type: str, symbol: str, price: float, sl: float, tp: float, lot: float, sentiment_label: str = "", extra: str = ""
    ):
        is_close = "CLOSE" in trade_type.upper()
        if is_close:
            icon = "🏁"
            action = "ปิดสถานะ"
            lines = [
                f"{icon} <b>{action} {self._sym(symbol)}</b>",
                f"💰 ราคาปิด: {price:.2f}  |  Lot: {lot}",
            ]
            if extra:
                lines.append(f"📊 ผลลัพธ์: <b>{extra}</b>")
        else:
            icon = "🟢" if "BUY" in trade_type.upper() else "🔴"
            action = "ซื้อ" if "BUY" in trade_type.upper() else "ขาย"
            paper = " [จำลอง]" if "PAPER" in trade_type.upper() else ""
            lines = [
                f"{icon} <b>{action} {self._sym(symbol)}{paper}</b>",
                f"💵 ราคา: {price:.2f}  |  Lot: {lot}",
                f"🛑 SL: {sl:.2f}  |  🎯 TP: {tp:.2f}",
            ]
            if sentiment_label:
                s_th = SENTIMENT_TH.get(sentiment_label, sentiment_label)
                lines.append(f"📰 Sentiment: {s_th}")
        await self._send("\n".join(lines))

    async def send_sentiment_alert(self, label: str, score: float, key_factors: list[str], symbol: str = ""):
        icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(label, "⚪")
        s_th = SENTIMENT_TH.get(label, label)
        sym_name = self._sym(symbol) if symbol else "ตลาด"
        factors = "\n".join(f"  • {f}" for f in key_factors[:4]) if key_factors else "  • ไม่มีข้อมูล"
        lines = [
            f"{icon} <b>วิเคราะห์ข่าว {sym_name}</b>",
            f"📊 ทิศทาง: <b>{s_th}</b> ({score:+.2f})",
            f"📌 ปัจจัยสำคัญ:\n{factors}",
        ]
        await self._send("\n".join(lines))

    async def send_optimization_report(self, assessment: str, confidence: float):
        lines = [
            "🤖 <b>รายงาน Optimization รายสัปดาห์</b>",
            f"📋 {assessment}",
            f"🎯 ความมั่นใจ: {confidence:.0%}",
        ]
        await self._send("\n".join(lines))

    async def send_daily_report(self, trades: int, pnl: float, win_rate: float):
        icon = "📈" if pnl >= 0 else "📉"
        pnl_color = "กำไร" if pnl >= 0 else "ขาดทุน"
        lines = [
            f"{icon} <b>สรุปผลประจำวัน</b>",
            f"📊 เทรด: {trades} ครั้ง  |  อัตราชนะ: {win_rate:.1%}",
            f"💰 {pnl_color}: <b>${abs(pnl):.2f}</b>",
        ]
        await self._send("\n".join(lines))

    async def send_message(self, text: str):
        await self._send(text)

    async def send_error_alert(self, error: str):
        lines = [
            "⚠️ <b>แจ้งเตือนข้อผิดพลาด</b>",
            f"❌ {error[:500]}",
        ]
        await self._send("\n".join(lines))

    async def send_health_alert(self, status: str, details: str):
        if status == "recovered":
            text = f"✅ <b>ระบบกลับมาปกติ</b>\n{details}"
        else:
            text = f"🚨 <b>ระบบมีปัญหา</b>\n{details}"
        await self._send(text)

    async def send_start_alert(self, symbol: str, timeframe: str, mode: str = "AI Autonomous"):
        sym_name = self._sym(symbol)
        lines = [
            "▶️ <b>เริ่มเทรด</b>",
            f"📈 สินค้า: {sym_name} ({symbol})",
            f"⏱ Timeframe: {timeframe}",
            f"🤖 โหมด: {mode}",
        ]
        await self._send("\n".join(lines))

    async def send_stop_alert(self, symbol: str = ""):
        sym_name = f" {self._sym(symbol)}" if symbol else ""
        await self._send(f"⏹ <b>หยุดเทรด{sym_name}</b>")
