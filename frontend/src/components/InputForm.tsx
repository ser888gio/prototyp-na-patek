import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SquarePen, Brain, Send, StopCircle, Save } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import FileUploader from "./UploadFile";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Updated InputFormProps
interface InputFormProps {
  onSubmit: (inputValue: string, effort: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  hasHistory: boolean;
  onSaveConversation?: (conversationId: string) => Promise<void>;
  currentConversationId?: string;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
  onSaveConversation,
  currentConversationId,
}) => {
  const [internalInputValue, setInternalInputValue] = useState("");
  const [effort, setEffort] = useState("medium");
  const [isSaving, setIsSaving] = useState(false);

  // Debug logging
  console.log('[DEBUG] InputForm render:', {
    hasHistory,
    onSaveConversation: !!onSaveConversation,
    currentConversationId,
    shouldShowSaveButton: hasHistory && onSaveConversation && currentConversationId
  });

  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!internalInputValue.trim()) return;
    onSubmit(internalInputValue, effort);
    setInternalInputValue("");
  };

  const handleSaveConversation = async () => {
    if (!onSaveConversation || !currentConversationId) return;

    setIsSaving(true);
    try {
      await onSaveConversation(currentConversationId);
    } catch (error) {
      console.error("Failed to save conversation:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit with Ctrl+Enter (Windows/Linux) or Cmd+Enter (Mac)
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleInternalSubmit();
    }
  };

  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className={`flex flex-col gap-2 p-3 pb-4`}
    >
      <div
        className={`flex flex-row items-center justify-between text-foreground rounded-3xl rounded-bl-sm ${
          hasHistory ? "rounded-br-sm" : ""
        } break-words min-h-7 bg-card border border-border px-4 pt-3 `}
      >
        <Textarea
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Prosím, zadejte Vaš dotaz"
          className={`w-full text-foreground placeholder-muted-foreground resize-none border-0 focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none bg-transparent
                        md:text-base  min-h-[56px] max-h-[200px]`}
          rows={1}
        />
        <div className="-mt-3">
          {isLoading ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-destructive hover:text-destructive/80 hover:bg-destructive/10 p-2 cursor-pointer rounded-full transition-all duration-200"
              onClick={onCancel}
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              variant="ghost"
              className={`${
                isSubmitDisabled
                  ? "text-muted-foreground"
                  : "text-primary hover:text-primary/80 hover:bg-primary/10"
              } p-2 cursor-pointer rounded-full transition-all duration-200 text-base`}
              disabled={isSubmitDisabled}
            >
              Search
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex flex-row gap-2">
          <div className="flex flex-row gap-2 bg-card border border-border text-foreground focus:ring-primary rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm">
              <Brain className="h-4 w-4 mr-2" />
              Effort
            </div>
            <Select value={effort} onValueChange={setEffort}>
              <SelectTrigger className="w-[120px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="Effort" />
              </SelectTrigger>
              <SelectContent className="bg-card border-border text-foreground cursor-pointer">
                <SelectItem
                  value="low"
                  className="hover:bg-muted focus:bg-muted cursor-pointer"
                >
                  Low
                </SelectItem>
                <SelectItem
                  value="medium"
                  className="hover:bg-muted focus:bg-muted cursor-pointer"
                >
                  Medium
                </SelectItem>
                <SelectItem
                  value="high"
                  className="hover:bg-muted focus:bg-muted cursor-pointer"
                >
                  High
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="flex gap-2">
          {hasHistory && onSaveConversation && currentConversationId && (
            <Button
              className="bg-card border-border text-foreground cursor-pointer rounded-xl rounded-t-sm pl-2 hover:bg-muted"
              variant="default"
              onClick={handleSaveConversation}
              disabled={isSaving}
            >
              <Save size={16} />
              {isSaving ? "Saving..." : "Save"}
            </Button>
          )}
          {hasHistory && (
            <Button
              className="bg-card border-border text-foreground cursor-pointer rounded-xl rounded-t-sm pl-2 hover:bg-muted"
              variant="default"
              onClick={() => window.location.reload()}
            >
              <SquarePen size={16} />
              New Search
            </Button>
          )}
        </div>
      </div>
      <FileUploader />
    </form>
  );
};
