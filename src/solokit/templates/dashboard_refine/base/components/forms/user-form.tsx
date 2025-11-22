"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { userSchema, type UserFormData } from "@/lib/validations";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/**
 * User Form Component
 *
 * Example form component demonstrating:
 * - react-hook-form integration
 * - Zod validation with zodResolver
 * - TypeScript type safety from Zod inference
 * - shadcn/ui components (Button, Card)
 * - Error handling and display
 *
 * This pattern can be adapted for any form in your dashboard.
 */

interface UserFormProps {
  // eslint-disable-next-line no-unused-vars
  onSubmit: (data: UserFormData) => Promise<void> | void;
  defaultValues?: Partial<UserFormData>;
  isLoading?: boolean;
}

export function UserForm({ onSubmit, defaultValues, isLoading }: UserFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues,
  });

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-2">
            Name
          </label>
          <input
            id="name"
            type="text"
            {...register("name")}
            className="w-full rounded-md border px-3 py-2 bg-background"
            disabled={isLoading}
          />
          {errors.name && <p className="mt-1 text-sm text-destructive">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2">
            Email
          </label>
          <input
            id="email"
            type="email"
            {...register("email")}
            className="w-full rounded-md border px-3 py-2 bg-background"
            disabled={isLoading}
          />
          {errors.email && <p className="mt-1 text-sm text-destructive">{errors.email.message}</p>}
        </div>

        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit"}
        </Button>
      </form>
    </Card>
  );
}
