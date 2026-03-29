import { useGetHealthQuery } from "@/store/api/energyApi";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

export function HealthCheck() {
  const { data, error, isLoading } = useGetHealthQuery();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Loader2 className="size-4 animate-spin" />
        <span>Checking server...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        <XCircle className="size-4" />
        <span>Server offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-green-600">
      <CheckCircle className="size-4" />
      <span>Server online</span>
    </div>
  );
}
