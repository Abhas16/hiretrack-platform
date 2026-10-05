import { z } from "zod";

/** One form for both modes; register mode additionally needs a name and an 8+ char password. */
export const authSchema = z
  .object({
    mode: z.enum(["login", "register"]),
    email: z.email("Enter a valid email"),
    password: z.string().min(1, "Enter your password").max(128),
    fullName: z.string().trim().max(120),
  })
  .superRefine((values, ctx) => {
    if (values.mode !== "register") return;
    if (!values.fullName) {
      ctx.addIssue({ code: "custom", path: ["fullName"], message: "Enter your name" });
    }
    if (values.password.length < 8) {
      ctx.addIssue({ code: "custom", path: ["password"], message: "At least 8 characters" });
    }
  });

export type AuthFormValues = z.infer<typeof authSchema>;
export type AuthMode = AuthFormValues["mode"];
