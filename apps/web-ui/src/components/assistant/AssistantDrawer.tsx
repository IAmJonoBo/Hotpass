/**
 * Assistant Drawer
 *
 * A right-hand drawer that can be opened from any page to access the assistant.
 */

import { AssistantChat } from './AssistantChat'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetBody } from '@/components/ui/sheet'

interface AssistantDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialMessage?: string
}

export function AssistantDrawer({ open, onOpenChange, initialMessage }: AssistantDrawerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader onClose={() => onOpenChange(false)}>
          <SheetTitle>Assistant</SheetTitle>
        </SheetHeader>
        <SheetBody className="p-0">
          <AssistantChat
            className="h-full border-0 rounded-none"
            initialMessage={initialMessage}
          />
        </SheetBody>
      </SheetContent>
    </Sheet>
  )
}
