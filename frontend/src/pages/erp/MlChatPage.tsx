import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Bot, User } from 'lucide-react'
import { mlService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'

interface ChatMessage {
  sender: 'user' | 'assistant'
  text: string
  timestamp: string
}

export const MlChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: 'Hello! I am your FinIntel Conversational Assistant. How can I help you analyze your revenue, inventory, or financial health today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')

  const chatMutation = useMutation({
    mutationFn: (msg: string) => mlService.chatAssistant(msg),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data?.message || 'I have analyzed your request based on current platform telemetry.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Sorry, I encountered an issue connecting to the AI inference service. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    },
  })

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    const userText = inputMessage.trim()
    setInputMessage('')
    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        text: userText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])

    chatMutation.mutate(userText)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary-600" />
          <span>Conversational Financial AI Assistant</span>
        </h1>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
          Ask natural language questions about your revenue forecasts, expense budgets, or inventory reorder points
        </p>
      </div>

      <Card className="h-[520px] flex flex-col justify-between overflow-hidden">
        <CardHeader className="border-b border-surface-100 dark:border-surface-800 py-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>FinIntel AI Copilot Online</span>
          </CardTitle>
          <CardDescription>Powered by FastAPI NLP & ML Prediction Models</CardDescription>
        </CardHeader>

        {/* Chat Messages Body */}
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                  msg.sender === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-surface-200 dark:bg-surface-800 text-surface-700 dark:text-surface-200'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-primary-600" />}
              </div>
              <div
                className={`max-w-[80%] p-3.5 rounded-2xl text-xs space-y-1 ${
                  msg.sender === 'user'
                    ? 'bg-primary-600 text-white rounded-tr-none'
                    : 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-surface-100 rounded-tl-none'
                }`}
              >
                <p className="leading-relaxed">{msg.text}</p>
                <p className="text-[9px] opacity-70 text-right">{msg.timestamp}</p>
              </div>
            </div>
          ))}

          {chatMutation.isPending && (
            <div className="flex items-center gap-2 text-xs text-surface-400 p-2">
              <Spinner size="sm" />
              <span>AI is processing your query...</span>
            </div>
          )}
        </CardContent>

        {/* Chat Input */}
        <div className="p-3 border-t border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50">
          <form onSubmit={handleSend} className="flex items-center gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask e.g. 'What is our projected revenue for next quarter?'"
              className="flex-1"
            />
            <Button variant="primary" type="submit" isLoading={chatMutation.isPending} leftIcon={<Send className="w-4 h-4" />}>
              Send
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
