"""
Simple command-line chat interface for testing the Business Intelligence Copilot.
Provides an interactive way to test the AI core functionality.
"""

import os
import sys
from datetime import datetime
from langchain_integration import business_agent


class SimpleChatInterface:
    """Simple command-line chat interface."""
    
    def __init__(self):
        """Initialize the chat interface."""
        self.session_id = f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.business_context = {}
        
    def display_welcome(self):
        """Display welcome message."""
        print("=" * 60)
        print("🤖 M32 BUSINESS INTELLIGENCE COPILOT")
        print("=" * 60)
        print("Welcome! I'm your AI business assistant.")
        print("I can help you with:")
        print("• Market research and competitor analysis")
        print("• Industry trends and insights")
        print("• Business strategy recommendations")
        print("• Data-driven decision making")
        print()
        print("Commands:")
        print("• Type your questions naturally")
        print("• '/context' - Set business context")
        print("• '/history' - View conversation history")
        print("• '/clear' - Clear conversation")
        print("• '/help' - Show this help")
        print("• '/quit' - Exit chat")
        print("=" * 60)
    
    def set_business_context(self):
        """Set business context interactively."""
        print("\n📋 Let's set up your business context:")
        
        company = input("Company name (optional): ").strip()
        if company:
            self.business_context["company"] = company
        
        industry = input("Industry/sector: ").strip()
        if industry:
            self.business_context["industry"] = industry
        
        business_type = input("Business type (e.g., B2B SaaS, e-commerce, consulting): ").strip()
        if business_type:
            self.business_context["business_type"] = business_type
        
        size = input("Company size (e.g., startup, small, medium): ").strip()
        if size:
            self.business_context["size"] = size
        
        print(f"\n✅ Business context updated: {self.business_context}")
    
    def display_history(self):
        """Display conversation history."""
        history = business_agent.get_conversation_history(self.session_id)
        
        if not history:
            print("\n📝 No conversation history yet.")
            return
        
        print(f"\n📝 Conversation History ({len(history)} messages):")
        print("-" * 40)
        
        for i, message in enumerate(history, 1):
            role_icon = "👤" if message.role == "user" else "🤖"
            print(f"{role_icon} {message.role.title()}: {message.content[:100]}...")
            if i < len(history):
                print()
    
    def process_message(self, message: str) -> bool:
        """Process user message and return whether to continue."""
        # Handle commands
        if message.startswith('/'):
            command = message.lower().strip()
            
            if command == '/quit':
                return False
            elif command == '/help':
                self.display_welcome()
                return True
            elif command == '/context':
                self.set_business_context()
                return True
            elif command == '/history':
                self.display_history()
                return True
            elif command == '/clear':
                business_agent.clear_conversation(self.session_id)
                print("✅ Conversation cleared!")
                return True
            else:
                print("❌ Unknown command. Type '/help' for available commands.")
                return True
        
        # Process regular message
        print("\n🤖 Thinking...")
        
        result = business_agent.chat(
            message,
            session_id=self.session_id,
            business_context=self.business_context if self.business_context else None
        )
        
        if result["status"] == "success":
            print(f"\n🤖 Business Intelligence Copilot:")
            print("-" * 40)
            print(result["response"])
            
            # Show tools used if any
            if result.get("tools_used"):
                print(f"\n🔧 Tools used: {', '.join(result['tools_used'])}")
            
            print(f"\n💬 Context: {result['context_length']} messages")
        else:
            print(f"\n❌ Sorry, I encountered an error: {result['error']}")
            print("Please try rephrasing your question or check your API configuration.")
        
        return True
    
    def run(self):
        """Run the interactive chat interface."""
        # Check configuration
        from config import validate_config
        config_status = validate_config()
        
        if config_status["status"] != "valid":
            print("❌ Error: Configuration invalid!")
            print(f"Error: {config_status['error']}")
            print("\nTo fix this:")
            print("1. Run: python3 setup_env.py (guided setup)")
            print("2. Or manually create .env file with your API key")
            return
        
        self.display_welcome()
        
        # Optional: Set initial business context
        setup_context = input("\nWould you like to set up your business context first? (y/n): ").strip().lower()
        if setup_context == 'y':
            self.set_business_context()
        
        print(f"\n💬 Chat started! Session ID: {self.session_id}")
        print("Type your message or '/help' for commands:\n")
        
        try:
            while True:
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                should_continue = self.process_message(user_input)
                
                if not should_continue:
                    break
                
                print()  # Add spacing between exchanges
                
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        print("👋 Thank you for using M32 Business Intelligence Copilot!")


def main():
    """Main function to run the chat interface."""
    chat = SimpleChatInterface()
    chat.run()


if __name__ == "__main__":
    main()
