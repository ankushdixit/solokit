/**
 * Validation Schemas
 *
 * This file contains Zod validation schemas for form inputs and API requests.
 * Using Zod provides:
 * - Runtime type validation
 * - TypeScript type inference
 * - Integration with react-hook-form via @hookform/resolvers
 * - Clear error messages for users
 */

import { z } from "zod";

/**
 * User validation schema
 * Used for user creation and update forms
 */
export const userSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be less than 100 characters"),
  email: z.string().email("Invalid email address"),
});

export type UserFormData = z.infer<typeof userSchema>;

/**
 * Product validation schema
 * Example for product management forms
 */
export const productSchema = z.object({
  name: z.string().min(1, "Product name is required").max(200),
  price: z.number().positive("Price must be positive"),
  description: z.string().min(10, "Description must be at least 10 characters").optional(),
  inStock: z.boolean().default(true),
});

export type ProductFormData = z.infer<typeof productSchema>;

/**
 * Order validation schema
 * Example for order processing forms
 */
export const orderSchema = z.object({
  userId: z.number().positive(),
  productId: z.number().positive(),
  quantity: z.number().int().positive("Quantity must be a positive integer"),
  notes: z.string().max(500, "Notes must be less than 500 characters").optional(),
});

export type OrderFormData = z.infer<typeof orderSchema>;
