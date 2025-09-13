import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, User, Bot } from 'lucide-react';
import { cn } from '../lib/utils';

interface ChatMessageProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp?: Date;
  isLoading?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  content, 
  role, 
  timestamp,
  isLoading = false 
}) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyToClipboard = async (text: string, codeId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(codeId);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  return (
    <div className={cn(
      "flex w-full mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "flex max-w-[85%] gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        {/* Avatar */}
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
          isUser 
            ? "bg-blue-600" 
            : isAssistant 
              ? "bg-gray-700" 
              : "bg-purple-600"
        )}>
          {isUser ? <User size={16} /> : isAssistant ? <Bot size={16} /> : "S"}
        </div>

        {/* Message Content */}
        <div className={cn(
          "rounded-2xl px-4 py-3 shadow-sm",
          isUser 
            ? "bg-blue-600 text-white" 
            : "bg-gray-100 text-gray-900 border border-gray-200"
        )}>
          {isLoading && isAssistant ? (
            <div className="flex items-center space-x-1">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-gray-500 text-sm ml-2">Thinking...</span>
            </div>
          ) : (
            <div className={cn(
              "prose prose-sm max-w-none",
              isUser 
                ? "prose-invert" 
                : "prose-gray"
            )}>
              {isUser ? (
                // Simple text rendering for user messages
                <div className="whitespace-pre-wrap">{content}</div>
              ) : (
                // Rich markdown rendering for assistant messages
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code: ({ node, inline, className, children, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      const language = match ? match[1] : '';
                      const codeString = String(children).replace(/\n$/, '');
                      const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

                      if (!inline && language) {
                        return (
                          <div className="relative group">
                            <div className="flex items-center justify-between bg-gray-800 text-gray-200 px-4 py-2 rounded-t-lg text-sm">
                              <span className="font-medium">{language}</span>
                              <button
                                onClick={() => copyToClipboard(codeString, codeId)}
                                className="flex items-center gap-1 px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 transition-colors"
                              >
                                {copiedCode === codeId ? (
                                  <>
                                    <Check size={14} />
                                    <span>Copied!</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy size={14} />
                                    <span>Copy</span>
                                  </>
                                )}
                              </button>
                            </div>
                            <SyntaxHighlighter
                              style={oneDark}
                              language={language}
                              PreTag="div"
                              className="!mt-0 !rounded-t-none"
                              {...props}
                            >
                              {codeString}
                            </SyntaxHighlighter>
                          </div>
                        );
                      }

                      return (
                        <code
                          className={cn(
                            "px-1.5 py-0.5 rounded text-sm font-mono",
                            isUser 
                              ? "bg-blue-500 text-white" 
                              : "bg-gray-200 text-gray-800"
                          )}
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    },
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
                        {children}
                      </blockquote>
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-4">
                        <table className="min-w-full border border-gray-300 rounded-lg">
                          {children}
                        </table>
                      </div>
                    ),
                    th: ({ children }) => (
                      <th className="border border-gray-300 px-4 py-2 bg-gray-50 font-semibold text-left">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-gray-300 px-4 py-2">
                        {children}
                      </td>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside space-y-1 my-2">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside space-y-1 my-2">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="text-sm leading-relaxed">
                        {children}
                      </li>
                    ),
                    a: ({ href, children }) => (
                      <a 
                        href={href} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {children}
                      </a>
                    ),
                    h1: ({ children }) => (
                      <h1 className="text-xl font-bold mt-6 mb-3 text-gray-900">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-lg font-semibold mt-5 mb-2 text-gray-800">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-base font-medium mt-4 mb-2 text-gray-800">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => (
                      <p className="leading-relaxed mb-3 last:mb-0">
                        {children}
                      </p>
                    ),
                  }}
                >
                  {content}
                </ReactMarkdown>
              )}
            </div>
          )}

          {/* Timestamp */}
          {timestamp && !isLoading && (
            <div className={cn(
              "text-xs mt-2 opacity-70",
              isUser ? "text-blue-100" : "text-gray-500"
            )}>
              {timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
