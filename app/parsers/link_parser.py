from app.parsers.base_parser import BaseParser, ParsedMessage, ParsedSession
from typing import List
import httpx
from bs4 import BeautifulSoup


class LinkParser(BaseParser):
    """
    Fetches and parses a shared AI conversation URL.
    Supports ChatGPT and Claude share links.
    """

    def parse(self, raw_input: str) -> ParsedSession:
        """
        Accepts a share link URL as a string.
        Fetches the page and extracts conversation messages.
        """
        try:
            url = raw_input.strip()
            platform = self._detect_platform(url)
            html = self._fetch_page(url)
            messages = self._extract_messages(html, platform)

            return ParsedSession(
                title=f"Shared {platform.title()} Conversation",
                source_platform=platform,
                input_method="share_link",
                messages=messages,
                message_count=len(messages),
                raw_input=url,
            )

        except Exception as e:
            raise ValueError(f"Failed to parse share link: {str(e)}")

    def _detect_platform(self, url: str) -> str:
        if "chatgpt.com" in url or "openai.com" in url:
            return "chatgpt"
        elif "claude.ai" in url:
            return "claude"
        else:
            return "unknown"

    def _fetch_page(self, url: str) -> str:
        """
        Fetches the HTML content of the share link page.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    def _extract_messages(self, html: str, platform: str) -> List[ParsedMessage]:
        """
        Extracts messages from the fetched HTML.
        Uses platform-specific selectors.
        """
        soup = BeautifulSoup(html, "html.parser")
        messages = []
        position = 0

        if platform == "chatgpt":
            # ChatGPT share pages use data-message-author-role attributes
            turns = soup.find_all(
                attrs={"data-message-author-role": True}
            )
            for turn in turns:
                role_attr = turn.get("data-message-author-role", "")
                if role_attr not in ("user", "assistant"):
                    continue
                content = self.clean_content(turn.get_text(separator="\n"))
                if not content:
                    continue
                messages.append(
                    ParsedMessage(
                        role=role_attr,
                        content=content,
                        position=position,
                        timestamp=None,
                    )
                )
                position += 1

        elif platform == "claude":
            # Claude share pages structure may vary
            # This targets the most common pattern
            turns = soup.find_all("div", class_=lambda c: c and "message" in c.lower())
            for turn in turns:
                class_str = " ".join(turn.get("class", []))
                if "human" in class_str or "user" in class_str:
                    role = "user"
                elif "assistant" in class_str or "bot" in class_str:
                    role = "assistant"
                else:
                    continue
                content = self.clean_content(turn.get_text(separator="\n"))
                if not content:
                    continue
                messages.append(
                    ParsedMessage(
                        role=role,
                        content=content,
                        position=position,
                        timestamp=None,
                    )
                )
                position += 1

        return messages