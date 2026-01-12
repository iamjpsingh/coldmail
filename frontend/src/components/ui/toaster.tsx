import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { X, CheckCircle2, AlertCircle } from "lucide-react"

export function Toaster() {
  const { toasts, dismiss } = useToast()

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm">
      {toasts.map((toast) => {
        const Icon = toast.variant === 'destructive' ? AlertCircle : CheckCircle2

        return (
          <div
            key={toast.id}
            data-state="open"
            className={cn(
              "pointer-events-auto relative flex items-start gap-3 rounded-lg border p-4 shadow-lg",
              "bg-card text-card-foreground",
              toast.variant === 'destructive' && "border-destructive/50 bg-destructive/10",
            )}
          >
            <Icon
              className={cn(
                "h-5 w-5 flex-shrink-0 mt-0.5",
                toast.variant === 'destructive' ? "text-destructive" : "text-green-500"
              )}
            />
            <div className="flex-1 space-y-1">
              {toast.title && (
                <p className="text-sm font-semibold">{toast.title}</p>
              )}
              {toast.description && (
                <p className="text-sm text-muted-foreground">{toast.description}</p>
              )}
            </div>
            <button
              onClick={() => dismiss(toast.id)}
              className="flex-shrink-0 rounded-md p-1 hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
