import React, { useState, useCallback, useEffect } from "react";
import { login, signup, getCurrentUser } from "../services/api";
import type { LoginCredentials, SignupCredentials } from "../types";

type AuthForm = LoginCredentials & Partial<Pick<SignupCredentials, "full_name" | "confirmPassword">>;

export const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [form, setForm] = useState<AuthForm>({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const isLogin = mode === "login";
  const isSignup = mode === "signup";
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setForm((prev) => ({ ...prev, [name]: value }));
    },
    [],
  );
  const handleTogglePassword = useCallback(() => setShowPassword((p) => !p), []);
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    let isValid = true;
    const email = form.email.trim();
    const password = form.password;
    if (!email) {
      newErrors.email = "Email is required";
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
      isValid = false;
    } else {
      delete newErrors.email;
    }
    if (!password) {
      newErrors.password = "Password is required";
      isValid = false;
    } else if (isSignup) {
      if (!form.full_name?.trim()) {
        newErrors.full_name = "Full name is required";
        isValid = false;
      } else {
        delete newErrors.full_name;
      }
      if (password.length < 8) {
        newErrors.password = "Password must be at least 8 characters";
        isValid = false;
      }
      const confirm = form.confirmPassword || "";
      if (!confirm) {
        newErrors.confirmPassword = "Please confirm your password";
        isValid = false;
      } else if (confirm !== password) {
        newErrors.confirmPassword = "Passwords do not match";
        isValid = false;
      }
    } else {
      delete newErrors.full_name;
      delete newErrors.confirmPassword;
    }
    setErrors(newErrors);
    return isValid;
  };
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;
      setIsSubmitting(true);
      setErrors({});
      try {
        if (isLogin) {
          await login({ email: form.email, password: form.password });
          // After login, redirect to chat page
          window.location.href = "/";
        } else {
          await signup({
            full_name: form.full_name || "",
            email: form.email,
            password: form.password,
          });
          setShowSuccess(true);
          // Reset form after 2 seconds
          setTimeout(() => {
            setMode("login");
            setForm({ email: "", password: "" });
            setShowSuccess(false);
          }, 2000);
        }
      } catch (err: any) {
        const detail =
          err.response?.data?.detail || err.message || "Authentication failed";
        setErrors({ form: detail });
      } finally {
        setIsSubmitting(false);
      }
    },
    [isLogin, form],
  );
  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        await getCurrentUser();
      } catch {
        // Not logged in - expected on the auth page.
      }
    };

    void checkCurrentUser();
  }, []);
  const inputClass =
    "inputField w-full rounded-lg border border-coffeeBrown/20 bg-coffeeBrown/5 py-3 pl-3 pr-12 text-coffeeBrown transition-colors focus:outline-none focus:border-coffeeBrown";
  const labelClass = "labelClass block text-sm font-medium text-coffeeBrown mb-1";
  return (
    <div className={showSuccess ? "min-h-screen flex items-center justify-center px-4 py-12" : "min-h-screen flex items-center justify-center px-4 py-12 coffee-bg"}>
      {showSuccess ? (
        <div className="text-center">
          <h1 className="text-5xl font-extrabold text-coffeeEspesso tracking-tight mb-4">Welcome!</h1>
          <p className="text-coffeeBrown/60 text-lg mb-6">Your account has been created successfully. You can now log in.</p>
          <button
            type="button"
            className="rounded-md px-6 py-3 text-sm font-medium text-coffeeEspesso bg-coffeeEspesso hover:bg-coffeeBrown transition-colors"
            onClick={() => setMode("login")}
          >
            Sign In
          </button>
        </div>
      ) : (
        <div className="w-full max-w-xl">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-extrabold text-coffeeEspesso tracking-tight">
            AI Lawyer
          </h1>
          <p className="text-coffeeBrown/60 text-lg mt-2">
            Your trusted legal companion
          </p>
        </div>
        {/* Mode toggle */}
        <div className="flex bg-coffeeBrown/5 rounded-lg p-1 mb-6">
          <button
            type="button"
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              isLogin
                ? "bg-coffeeEspesso text-coffee-cream"
                : "text-coffeeBrown hover:text-coffeeBrown hover:bg-coffeeBrown/10"
            }`}
            onClick={() => setMode("login")}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              isSignup
                ? "bg-coffeeEspesso text-coffee-cream"
                : "text-coffeeBrown hover:text-coffeeBrown hover:bg-coffeeBrown/10"
            }`}
            onClick={() => setMode("signup")}
          >
            Create Account
          </button>
        </div>
        {/* Form */}
        <form onSubmit={handleSubmit} noValidate>
          {isSignup && (
            <div className="mb-4">
              <label className={labelClass} htmlFor="fullName">
                Full Name
              </label>
              <input
                id="fullName"
                name="full_name"
                type="text"
                className={inputClass}
                placeholder="John Doe"
                value={form.full_name || ""}
                onChange={handleChange}
                disabled={isSubmitting}
              />
              {errors.full_name && (
                <p className="text-error text-xs mt-1">{errors.full_name}</p>
              )}
            </div>
          )}
          <div className="mb-4">
            <label className={labelClass} htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className={inputClass}
              placeholder="john@example.com"
              value={form.email}
              onChange={handleChange}
              disabled={isSubmitting}
            />
            {errors.email && <p className="text-error text-xs mt-1">{errors.email}</p>}
          </div>
          <div className="mb-4">
            <label className={labelClass} htmlFor="password">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                className="block w-full rounded-md border-coffee-border bg-coffee-input py-2 px-3 text-coffee-foreground placeholder-coffee-muted focus:border-coffee-primary focus:outline-none focus:ring-2 focus:ring-coffee-primary focus:ring-offset-coffee-input"
                placeholder="•••••••"
                value={form.password}
                onChange={handleChange}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-3 top-1/2 -translate-y-1/2 text-coffee-muted hover:text-coffee-primary"
                tabIndex={-1}
                onClick={handleTogglePassword}
              >
                {showPassword ? (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M3 12h2m16 0h2M4.22 19.78l1.42-1.42M16.94 7.06l1.42-1.42" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-3-3m0 0l3-3m-3 3h8M3 17h8v-3" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M3 12h2m16 0h2M4.22 19.78l1.42-1.42M16.94 7.06l1.42-1.42" />
                  </svg>
                )}
              </button>
            </div>
            {errors.password && <p className="text-error text-xs mt-1">{errors.password}</p>}
          </div>
          {isSignup && (
            <div className="mb-6">
              <label htmlFor="confirmPassword">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                className="block w-full rounded-md border-coffee-border bg-coffee-input py-2 px-3 text-coffee-foreground placeholder-coffee-muted focus:border-coffee-primary focus:outline-none focus:ring-2 focus:ring-coffee-primary focus:ring-offset-coffee-input"
                placeholder="•••••••"
                value={form.confirmPassword || ""}
                onChange={handleChange}
                disabled={isSubmitting}
              />
              {errors.confirmPassword && (
                <p className="text-error text-xs mt-1">{errors.confirmPassword}</p>
              )}
            </div>
          )}
          {errors.form && <p className="text-error text-sm mb-4">{errors.form}</p>}
          <button
            type="submit"
            className="w-full py-3 px-4 bg-coffee-primary text-coffee-foreground rounded-md hover:bg-coffee-primary-hover transition-colors"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
        {!isLogin && (
          <p className="text-coffee-muted text-center text-sm mt-6">
            Already have an account?{" "}
            <button
              type="button"
              className="font-medium text-coffeeBrown hover:underline"
              onClick={() => setMode("login")}
            >
              Sign in
            </button>
          </p>
        )}
        {isLogin && (
          <p className="text-coffee-muted text-center text-sm mt-6">
            Don't have an account?{" "}
            <button
              type="button"
              className="font-medium text-coffeeBrown hover:underline"
              onClick={() => setMode("signup")}
            >
              Sign up
            </button>
          </p>
        )}
        </div>
      )}
      </div>
   
  );
};
