"""
Search view - user interface
"""

from typing import Dict, Any
from colorama import init, Fore, Style
from Source_code.controllers.search_controller import SearchController
from Source_code.utils.logger import logger

init(autoreset=True)  # Initialize colorama


class SearchView:
    """Command-line interface for search"""

    def __init__(self):
        self.controller = SearchController()

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

                # Perform search
                result = self.controller.search(query)
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