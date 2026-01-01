"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Sparkles, Send, Loader2 } from "lucide-react";
import { getAIRecommendations } from "@/lib/api";

export function AIConciergeCTA() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const recommendation = await getAIRecommendations(query);
      setResult(recommendation);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to get recommendations",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="overflow-hidden border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-purple-600 p-2">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl">Not sure where to start?</CardTitle>
            <CardDescription className="text-base">
              Describe your project, and our AI will recommend the best agents
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g., "I need to build a chatbot that answers questions from PDFs"'
              className="flex-1"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !query.trim()}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Ask AI
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {result && (
            <div className="rounded-md bg-white p-4 shadow-sm">
              <div className="prose prose-sm max-w-none">
                {result.split("\n").map((line, i) => (
                  <p key={i} className="mb-2 last:mb-0">
                    {line}
                  </p>
                ))}
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
