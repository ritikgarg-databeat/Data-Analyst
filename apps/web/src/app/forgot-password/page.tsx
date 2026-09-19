import Link from "next/link";

import { AuthCard } from "@/components/features/auth/auth-card";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  return <AuthCard title="Password recovery" description="This localhost version does not send email.">
    <div className="space-y-4 text-sm"><p>Contact an administrator and ask for a temporary password. It is shown once, expires after 24 hours, and must be replaced immediately after sign-in.</p>
      <p className="text-muted-foreground">If the only administrator is locked out, use the local recovery command documented in the setup guide.</p>
      <Button asChild className="w-full"><Link href="/login">Back to sign in</Link></Button></div>
  </AuthCard>;
}
