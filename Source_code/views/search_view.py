"""
Search view - user interface
"""

import os
import sys
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from colorama import init, Fore, Style
from Source_code.controllers.search_controller import SearchController
from Source_code.controllers.sync_controller import SyncController
from Source_code.utils.logger import logger

init(autoreset=True)  # Initialize colorama


class SearchView:
    """Command-line interface for search"""

    def __init__(self):
        self._sync_semantic_vectors_on_startup()
        self.controller = SearchController()

    def _sync_semantic_vectors_on_startup(self):
        """Refresh Elasticsearch documents with semantic vectors before searching."""
        try:
            print(f"{Fore.CYAN}Preparing semantic search index...{Style.RESET_ALL}")
            result = SyncController().sync_semantic_vectors()
            print(
                f"{Fore.GREEN}Semantic index ready: "
                f"{result.get('synced', 0)}/{result.get('total', 0)} emails synced{Style.RESET_ALL}"
            )
        except Exception as e:
            logger.error(f"Startup semantic sync failed: {e}")
            print(f"{Fore.YELLOW}Semantic startup sync failed; continuing with existing index.{Style.RESET_ALL}")

    def run_interactive(self):
        """Run interactive search session"""
        self._print_header()

        while True:
            try:
                query = input(f"\n{Fore.CYAN}🔎 Search{Style.RESET_ALL} (or 'quit'): ").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                    break

                if not query:
                    continue

                result = self.controller.semantic_search_text(query)
                if result['total'] == 0:
                    result = self.controller.search_words(query, ordered=False)
                self._print_results(result)

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted. Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                logger.error(f"Search error: {e}")
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

    def _print_header(self):
        """Print application header"""
        print(f"""
{Fore.CYAN}{'=' * 60}
{Fore.GREEN}🐘 Persian Email Search System v1.0
{Fore.CYAN}{'=' * 60}
{Fore.WHITE}Enter Persian words to search your emails
{Fore.YELLOW}Examples: گزارش | پروژه | فارسی | جستجو
{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}
        """)

    def _print_results(self, result: Dict[str, Any]):
        """Print search results"""
        total = result['total']
        query = result['query']

        if total == 0:
            print(f"{Fore.YELLOW}❌ No results found for '{query}'{Style.RESET_ALL}")
            return

        print(f"\n{Fore.GREEN}✅ Found {total} result(s) for '{query}':{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 50}{Style.RESET_ALL}")

        for i, email in enumerate(result['results'], 1):
            print(f"\n{Fore.WHITE}{i}. {Fore.YELLOW}📧 {email.get('subject', 'No subject')[:60]}{Style.RESET_ALL}")
            print(f"   {Fore.BLUE}From:{Style.RESET_ALL} {email.get('from', 'Unknown')[:40]}")
            print(f"   {Fore.BLUE}Score:{Style.RESET_ALL} {email.get('score', 0):.2f}")

            body = email.get('body', '')[:150]
            if body:
                print(f"   {Fore.BLUE}Body:{Style.RESET_ALL} {body}...")

            if 'highlights' in email and 'body' in email['highlights']:
                highlight = email['highlights']['body'][0][:100]
                print(f"   {Fore.MAGENTA}Match:{Style.RESET_ALL} {highlight}...")

        print(f"\n{Fore.CYAN}{'-' * 50}{Style.RESET_ALL}")


# ============= IMPORTANT: This runs the interactive search =============
if __name__ == "__main__":
    # Create the view and start interactive search
    view = SearchView()
    view.run_interactive()
