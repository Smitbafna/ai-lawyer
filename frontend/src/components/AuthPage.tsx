import React, { useState, useCallback, useEffect } from "react";
import { login, signup, getCurrentUser } from "../services/api";
import type { LoginCredentials, SignupCredentials } from "../types";
import { Button } from "../components/ui/button";

type AuthForm = LoginCredentials & Partial<Pick<SignupCredentials, "full_name" | "confirmPassword">>;

type AuthPageProps = {
  onLogin?: (auth: boolean) => void;
};

export const AuthPage: React.FC<AuthPageProps> = ({ onLogin }) => {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [form, setForm] = useState<AuthForm>({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const isLogin = mode === "login";
  const isSignup = mode === "signup";

  const switchMode = useCallback((m: "login" | "signup") => {
    setMode(m);
    setErrors({});
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }, []);

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
    }

    if (!password) {
      newErrors.password = "Password is required";
      isValid = false;
    } else if (isSignup) {
      if (password.length < 8) {
        newErrors.password = "Password must be at least 8 characters";
        isValid = false;
      }
    }

    if (isSignup) {
      if (!form.full_name?.trim()) {
        newErrors.full_name = "Full name is required";
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
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = useCallback(
    async (e?: React.SyntheticEvent) => {
      e?.preventDefault();
      if (isSubmitting || !validate()) return;
      setIsSubmitting(true);
      setErrors({});
      try {
        if (isLogin) {
          await login({ email: form.email, password: form.password });
          // Notify parent about login success
          onLogin?.(true);
          // Check for token directly - storage event may not fire in same context
          const token = localStorage.getItem("auth_token");
          if (token) {
            // Dispatch a custom event so main.tsx listener can detect it
            window.dispatchEvent(new StorageEvent("storage", { key: "auth_token", newValue: token }));
          }
        } else {
          await signup({
            full_name: form.full_name || "",
            email: form.email,
            password: form.password,
          });
          setShowSuccess(true);
          setTimeout(() => {
            setMode("login");
            setForm({ email: "", password: "" });
            setShowSuccess(false);
          }, 2000);
        }
      } catch (err: any) {
        const detail = err.response?.data?.detail || err.message || "Authentication failed";
        setErrors({ form: detail });
      } finally {
        setIsSubmitting(false);
      }
    },
    [isLogin, form, isSubmitting],
  );

  // Since there is no native submit button, Enter inside a field submits the form.
  const handleFormKeyDown = (e: React.KeyboardEvent<HTMLFormElement>) => {
    if (e.key === "Enter") handleSubmit(e);
  };

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
    "inputField w-full rounded-lg border border-coffeeBrown/20 bg-coffeeBrown/5 py-3 pl-3 pr-12 text-coffeeBrown transition-colors focus:outline-none focus:border-coffeeBrown disabled:opacity-60";
  const labelClass = "labelClass block text-sm font-medium text-coffeeBrown mb-1";

  return (
    <div
      className={
        showSuccess
          ? "min-h-screen flex items-center justify-center px-4 py-12"
          : "min-h-screen flex items-center justify-center px-4 py-12 coffee-bg"
      }
    >
      {showSuccess ? (
        <div className="text-center">
          <h1 className="text-5xl font-extrabold text-coffeeEspesso tracking-tight mb-4">Welcome!</h1>
          <p className="text-coffeeBrown/60 text-lg mb-6">
            Your account has been created successfully. You can now log in.
          </p>
          <Button onClick={() => switchMode("login")}>Sign In</Button>
        </div>
      ) : (
        <div className="w-full max-w-xl">
          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-5xl font-extrabold text-coffeeEspesso tracking-tight">AI Lawyer</h1>
            <p className="text-coffeeBrown/60 text-lg mt-2">Your trusted legal companion</p>
          </div>

          {/* Mode toggle */}
          <div className="mx-auto mb-6 flex w-fit gap-1 rounded-lg bg-coffeeBrown/5 p-1">
            <Button
              size="sm"
              variant={isLogin ? "default" : "default"}
              onClick={() => switchMode("login")}
            >
              Sign In
            </Button>
            <Button
              size="sm"
              variant={isSignup ? "default" : "default"}
              onClick={() => switchMode("signup")}
            >
              Create Account
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} onKeyDown={handleFormKeyDown} noValidate>
            {isSignup && (
              <div className="mb-4">
                <label className={labelClass} htmlFor="fullName">Full Name</label>
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
                {errors.full_name && <p className="text-error text-xs mt-1">{errors.full_name}</p>}
              </div>
            )}

            <div className="mb-4">
              <label className={labelClass} htmlFor="email">Email address</label>
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
              <label className={labelClass} htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  className={inputClass}
                  placeholder="•••••••"
                  value={form.password}
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <Button
                    size="icon"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={handleTogglePassword}
                  >
                    {showPassword ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    )}
                  </Button>
                </div>
              </div>
              {errors.password && <p className="text-error text-xs mt-1">{errors.password}</p>}
            </div>

            {isSignup && (
              <div className="mb-6">
                <label className={labelClass} htmlFor="confirmPassword">Confirm Password</label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  className={inputClass}
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

            <div className="flex justify-center">
              <Button className="min-w-[10rem]" loading={isSubmitting} onClick={() => handleSubmit()}>
                {isSubmitting ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
              </Button>
            </div>
          </form>

          <p className="text-coffee-muted text-center text-sm mt-6">
            {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
            <Button variant="link" className="inline" onClick={() => switchMode(isLogin ? "signup" : "login")}>
              {isLogin ? "Sign up" : "Sign in"}
            </Button>
          </p>
        </div>
      )}
    </div>
  );
};