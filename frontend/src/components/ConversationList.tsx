import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Plus,
  Archive,
  Trash2,
  MessageSquare,
  Calendar,
} from "lucide-react";

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  status: "active" | "archived" | "deleted";
  summary?: string;
}

interface ConversationListProps {
  currentConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onCreateConversation: () => void;
  userId?: string;
}

export function ConversationList({
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  userId,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [showArchived, setShowArchived] = useState(false);

  const API_BASE = import.meta.env.DEV
    ? "http://localhost:2024"
    : "http://localhost:8123";

  // Fetch conversations
  const fetchConversations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (userId) params.append("user_id", userId);
      if (searchQuery) params.append("search", searchQuery);
      params.append("limit", "50");

      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations?${params.toString()}`
      );

      if (response.ok) {
        const data = await response.json();
        const filteredConversations = showArchived
          ? data
          : data.filter((conv: Conversation) => conv.status === "active");
        setConversations(filteredConversations);
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    } finally {
      setLoading(false);
    }
  };

  // Archive conversation
  const archiveConversation = async (conversationId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}?archive_only=true`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchConversations();
      }
    } catch (error) {
      console.error("Failed to archive conversation:", error);
    }
  };

  // Delete conversation
  const deleteConversation = async (conversationId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this conversation? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await fetchConversations();
        // If current conversation was deleted, create a new one
        if (conversationId === currentConversationId) {
          onCreateConversation();
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffInHours < 168) {
      // 7 days
      return date.toLocaleDateString([], {
        weekday: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } else {
      return date.toLocaleDateString([], { month: "short", day: "numeric" });
    }
  };

  // Effect for fetching conversations
  useEffect(() => {
    fetchConversations();
  }, [searchQuery, showArchived, userId]);

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Conversations
          </CardTitle>
          <Button
            onClick={onCreateConversation}
            size="sm"
            className="flex items-center gap-1"
          >
            <Plus className="h-4 w-4" />
            New
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filter toggles */}
        <div className="flex gap-2">
          <Button
            variant={!showArchived ? "default" : "outline"}
            size="sm"
            onClick={() => setShowArchived(false)}
          >
            Active
          </Button>
          <Button
            variant={showArchived ? "default" : "outline"}
            size="sm"
            onClick={() => setShowArchived(true)}
          >
            <Archive className="h-4 w-4 mr-1" />
            Archived
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-full">
          {loading ? (
            <div className="p-4 text-center text-muted-foreground">
              Loading conversations...
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              {searchQuery ? "No conversations found" : "No conversations yet"}
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`group p-3 rounded-lg cursor-pointer transition-colors hover:bg-muted ${
                    currentConversationId === conversation.id
                      ? "bg-muted border border-border"
                      : ""
                  }`}
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm truncate">
                        {conversation.title}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {conversation.message_count} messages
                        </Badge>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(conversation.updated_at)}
                        </span>
                      </div>
                      {conversation.summary && (
                        <p className="text-xs text-muted-foreground mt-1 truncate">
                          {conversation.summary}
                        </p>
                      )}
                    </div>

                    {/* Actions (visible on hover) */}
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {conversation.status === "active" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            archiveConversation(conversation.id);
                          }}
                          className="h-7 w-7 p-0"
                        >
                          <Archive className="h-3 w-3" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(conversation.id);
                        }}
                        className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
