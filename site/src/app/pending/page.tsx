import { SignOutButton } from '@/components/sign-out-button';

export default function PendingPage() {
  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4 rounded-xl border p-6 text-center">
        <h1 className="text-2xl font-bold">ההרשמה ממתינה לאישור</h1>
        <p className="text-fd-muted-foreground">
          החשבון נוצר בהצלחה. הגישה לחומרי הקורס תיפתח לאחר שהמרצה תאשר את ההרשמה. אחרי האישור צריך להתחבר מחדש או לרענן את הדף.
        </p>
        <SignOutButton />
      </div>
    </main>
  );
}
