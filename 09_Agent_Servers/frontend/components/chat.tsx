"use client";

import { useEffect, useRef, useState } from "react";
import { useStream } from "@langchain/react";
import {
  Bot,
  FileText,
  Loader2,
  Search,
  Send,
  User,
  Wrench,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageHeader,
} from "@/components/ui/message";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { getMessageText, toolLabel } from "@/lib/messages";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

type StreamMessage = ReturnType<typeof useStream>["messages"][number];

const SUGGESTIONS = [
  "How often should I deworm my cat?",
  "What vaccinations do kittens need?",
  "What are signs of feline dehydration?",
];

function toolIcon(name?: string) {
  if (name === "retrieve_information") return <FileText className="size-3" />;
  if (name?.startsWith("tavily")) return <Search className="size-3" />;
  return <Wrench className="size-3" />;
}

export function Chat({ assistantId }: { assistantId: string }) {
  const stream = useStream({ apiUrl: API_URL, assistantId });
  const { messages, isLoading, error } = stream;

  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const send = (text: string) => {
    const content = text.trim();
    if (!content || isLoading) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ScrollArea className="flex-1">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
          {messages.length === 0 && (
            <div className="mt-10 flex flex-col items-center gap-6 text-center">
              <div className="flex size-14 items-center justify-center rounded-full bg-muted">
                <Bot className="size-7 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-medium">Ask the cat health agent</h2>
                <p className="text-sm text-muted-foreground">
                  Streams from your LangGraph deployment via a secure proxy.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <Button
                    key={s}
                    variant="outline"
                    size="sm"
                    onClick={() => send(s)}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, i) => (
            <MessageRow key={message.id ?? i} message={message} />
          ))}

          {isLoading && <ThinkingRow />}

          {error != null && (
            <Card className="border-destructive/40">
              <CardContent className="text-sm text-destructive">
                {error instanceof Error ? error.message : "Something went wrong."}
              </CardContent>
            </Card>
          )}

          <div ref={endRef} />
        </div>
      </ScrollArea>

      <div className="border-t bg-background">
        <form
          onSubmit={onSubmit}
          className="mx-auto flex w-full max-w-3xl items-center gap-2 px-4 py-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message the agent..."
            disabled={isLoading}
            className="h-10"
            autoFocus
          />
          <Button
            type="submit"
            size="lg"
            disabled={isLoading || input.trim().length === 0}
            className="h-10"
          >
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

function MessageRow({ message }: { message: StreamMessage }) {
  const isHuman = message.type === "human";
  const isTool = message.type === "tool";
  const text = getMessageText(message.content);
  const toolCalls =
    message.type === "ai"
      ? (message as unknown as {
          tool_calls?: Array<{ name?: string; id?: string }>;
        }).tool_calls ?? []
      : [];

  if (isTool) {
    return (
      <div className="mx-auto w-full max-w-3xl">
        <details className="group rounded-lg border bg-muted/40 text-sm">
          <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-muted-foreground">
            {toolIcon(message.name)}
            <span className="font-medium text-foreground">
              {toolLabel(message.name)}
            </span>
            <span className="text-xs">tool result</span>
          </summary>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap px-3 pb-3 text-xs text-muted-foreground">
            {text}
          </pre>
        </details>
      </div>
    );
  }

  return (
    <Message align={isHuman ? "end" : "start"}>
      <MessageAvatar>
        <Avatar>
          <AvatarFallback>
            {isHuman ? (
              <User className="size-4" />
            ) : (
              <Bot className="size-4" />
            )}
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>

      <MessageContent>
        {toolCalls.length > 0 && (
          <MessageHeader className="flex-wrap gap-1.5 px-0">
            {toolCalls.map((tc, idx) => (
              <Badge key={tc.id ?? idx} variant="secondary">
                {toolIcon(tc.name)}
                {toolLabel(tc.name)}
              </Badge>
            ))}
          </MessageHeader>
        )}

        {text && (
          <Bubble variant={isHuman ? "default" : "muted"}>
            <BubbleContent>
              {isHuman ? (
                <span className="whitespace-pre-wrap">{text}</span>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">{children}</ul>,
                    ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">{children}</ol>,
                    li: ({ children }) => <li>{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    code: ({ children, className }) => {
                      const isBlock = className?.includes("language-");
                      return isBlock ? (
                        <code className={cn("block rounded-md bg-black/10 dark:bg-white/10 px-3 py-2 font-mono text-xs overflow-x-auto", className)}>{children}</code>
                      ) : (
                        <code className="rounded bg-black/10 dark:bg-white/10 px-1 py-0.5 font-mono text-xs">{children}</code>
                      );
                    },
                    pre: ({ children }) => <pre className="mb-2 last:mb-0 overflow-x-auto">{children}</pre>,
                    blockquote: ({ children }) => <blockquote className="mb-2 border-l-2 border-current pl-3 opacity-70 last:mb-0">{children}</blockquote>,
                    h1: ({ children }) => <h1 className="mb-2 text-base font-bold">{children}</h1>,
                    h2: ({ children }) => <h2 className="mb-2 text-sm font-bold">{children}</h2>,
                    h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{children}</h3>,
                    a: ({ children, href }) => <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:opacity-80">{children}</a>,
                  }}
                >
                  {text}
                </ReactMarkdown>
              )}
            </BubbleContent>
          </Bubble>
        )}
      </MessageContent>
    </Message>
  );
}

function ThinkingRow() {
  return (
    <Message align="start">
      <MessageAvatar>
        <Avatar>
          <AvatarFallback>
            <Bot className="size-4" />
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <Bubble variant="muted">
          <BubbleContent className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Thinking...
          </BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
  );
}
