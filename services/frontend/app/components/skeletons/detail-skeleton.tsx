import { Card, CardContent, CardHeader } from "~/components/ui/card";
import { Skeleton } from "~/components/ui/skeleton";

export function DetailSkeleton() {
    return (
        <div className="max-w-2xl mx-auto space-y-4">
            <Skeleton className="h-6 w-32" />
            <Card>
                <CardHeader className="pb-2">
                    <Skeleton className="h-4 w-20" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-20 w-full" />
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="pb-2">
                    <Skeleton className="h-4 w-20" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-20 w-full" />
                </CardContent>
            </Card>
        </div>
    );
}
