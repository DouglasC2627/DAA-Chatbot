'use client';

import { useChatSettingsStore, DEFAULT_CHAT_SETTINGS, DEFAULT_UI_PREFERENCES } from '@/stores/chatSettingsStore';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RotateCcw, Settings2 } from 'lucide-react';

interface ChatSettingsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function ChatSettingsPanel({ open, onOpenChange }: ChatSettingsPanelProps) {
  const { chatSettings, uiPreferences, updateChatSettings, updateUIPreferences, resetToDefaults } =
    useChatSettingsStore();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Chat Settings
          </SheetTitle>
          <SheetDescription>
            Configure chat behavior and UI preferences
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-8rem)] mt-6 pr-4">
          <div className="space-y-6">
            {/* Chat Settings Section */}
            <div className="space-y-4">
              <div className="border-b pb-2">
                <h3 className="text-sm font-semibold">RAG Parameters</h3>
                <p className="text-xs text-muted-foreground">
                  Control how the AI retrieves and generates responses
                </p>
              </div>

              {/* Top-K Sources */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="top-k" className="text-sm font-medium">
                    Top-K Sources
                  </Label>
                  <span className="text-sm text-muted-foreground">{chatSettings.topK}</span>
                </div>
                <Slider
                  id="top-k"
                  min={1}
                  max={10}
                  step={1}
                  value={[chatSettings.topK]}
                  onValueChange={(value) => updateChatSettings({ topK: value[0] })}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Number of source chunks to retrieve from your documents
                </p>
              </div>

              {/* Temperature */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="temperature" className="text-sm font-medium">
                    Temperature
                  </Label>
                  <span className="text-sm text-muted-foreground">
                    {chatSettings.temperature.toFixed(2)}
                  </span>
                </div>
                <Slider
                  id="temperature"
                  min={0}
                  max={1}
                  step={0.01}
                  value={[chatSettings.temperature]}
                  onValueChange={(value) => updateChatSettings({ temperature: value[0] })}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Controls response creativity (0 = focused, 1 = creative)
                </p>
              </div>

              {/* Max Tokens */}
              <div className="space-y-2">
                <Label htmlFor="max-tokens" className="text-sm font-medium">
                  Max Tokens
                </Label>
                <Input
                  id="max-tokens"
                  type="number"
                  min={100}
                  max={4000}
                  step={100}
                  value={chatSettings.maxTokens}
                  onChange={(e) =>
                    updateChatSettings({ maxTokens: parseInt(e.target.value, 10) })
                  }
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum response length (100-4000 tokens)
                </p>
              </div>

              {/* History Length */}
              <div className="space-y-2">
                <Label htmlFor="history-length" className="text-sm font-medium">
                  Conversation History
                </Label>
                <Select
                  value={chatSettings.historyLength.toString()}
                  onValueChange={(value) =>
                    updateChatSettings({ historyLength: parseInt(value, 10) })
                  }
                >
                  <SelectTrigger id="history-length">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">None (stateless)</SelectItem>
                    <SelectItem value="3">Last 3 turns</SelectItem>
                    <SelectItem value="5">Last 5 turns (default)</SelectItem>
                    <SelectItem value="10">Last 10 turns</SelectItem>
                    <SelectItem value="15">Last 15 turns</SelectItem>
                    <SelectItem value="20">Last 20 turns</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Number of conversation turns to include in context
                </p>
              </div>
            </div>

            {/* UI Preferences Section */}
            <div className="space-y-4">
              <div className="border-b pb-2">
                <h3 className="text-sm font-semibold">UI Preferences</h3>
                <p className="text-xs text-muted-foreground">
                  Customize the chat interface appearance
                </p>
              </div>

              {/* Font Size */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="font-size" className="text-sm font-medium">
                    Font Size
                  </Label>
                  <span className="text-sm text-muted-foreground">
                    {uiPreferences.fontSize}px
                  </span>
                </div>
                <Slider
                  id="font-size"
                  min={12}
                  max={20}
                  step={1}
                  value={[uiPreferences.fontSize]}
                  onValueChange={(value) => updateUIPreferences({ fontSize: value[0] })}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Adjust message text size (12-20px)
                </p>
              </div>

              {/* Message View Mode */}
              <div className="space-y-2">
                <Label htmlFor="message-view" className="text-sm font-medium">
                  Message View
                </Label>
                <Select
                  value={uiPreferences.messageView}
                  onValueChange={(value: 'comfortable' | 'compact') =>
                    updateUIPreferences({ messageView: value })
                  }
                >
                  <SelectTrigger id="message-view">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="comfortable">Comfortable</SelectItem>
                    <SelectItem value="compact">Compact</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Choose message spacing and padding
                </p>
              </div>

              {/* Source References Default State */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="sources-expanded" className="text-sm font-medium">
                    Expand Sources by Default
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Show source references expanded when new messages arrive
                  </p>
                </div>
                <Switch
                  id="sources-expanded"
                  checked={uiPreferences.sourceReferencesExpanded}
                  onCheckedChange={(checked) =>
                    updateUIPreferences({ sourceReferencesExpanded: checked })
                  }
                />
              </div>
            </div>

            {/* Reset Button */}
            <div className="pt-4 border-t">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  resetToDefaults();
                }}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset to Defaults
              </Button>
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
