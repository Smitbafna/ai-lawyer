import React, { useRef, useEffect, useState } from "react"

interface TypewriterProps {
  text: string
  /** Number of characters to reveal per batch (default: 3) */
  batchSize?: number
  /** Delay between batches in ms (default: 50) */
  delay?: number
  /** Optional className for the container */
  className?: string
  /** Optional style overrides */
  style?: React.CSSProperties
}

/**
 * Typewriter effect that progressively reveals text.
 * Batches characters for a smooth, natural reveal (not terminal-style).
 * Respects prefers-reduced-motion.
 * Screen readers access the full text via aria-label.
 * Skip button available to immediately show complete text.
 */
export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  batchSize = 3,
  delay = 50,
  className: classNameProp,
  style,
}) => {
  const [displayedText, setDisplayedText] = useState("")
  const [isComplete, setIsComplete] = useState(false)
  const timerRef = useRef<number | null>(null)
  const skippedRef = useRef<boolean>(false)

  useEffect(() => {
    // Reset state when text changes
    setDisplayedText("")
    setIsComplete(false)
    skippedRef.current = false

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches

    if (prefersReducedMotion) {
      // Immediately show full text without animation
      setDisplayedText(text)
      setIsComplete(true)
      return
    }

    let chars = text
    let i = 0
    const revealBatch = () => {
      if (skippedRef.current) {
        setDisplayedText(text)
        setIsComplete(true)
        return
      }

      if (i < chars.length) {
        // Reveal a batch of characters (word-aware batching)
        const end = Math.min(i + batchSize, chars.length)
        // Adjust batch end at word boundary for natural flow
        if (end < chars.length) {
          const lastSpace = chars.lastIndexOf(" ", end)
          if (lastSpace > i) {
            setDisplayedText(chars.substring(0, lastSpace + 1))
            i = lastSpace + 1
          } else {
            setDisplayedText(chars.substring(0, end))
            i = end
          }
        } else {
          setDisplayedText(text)
          i = chars.length
          setIsComplete(true)
        }
        timerRef.current = setTimeout(revealBatch, delay)
      } else if (!skippedRef.current) {
        setIsComplete(true)
      }
    }

    revealBatch()

    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current)
      }
    }
  }, [text, batchSize, delay])

  // Handle skip click - immediately reveal full text
  const handleSkip = () => {
    skippedRef.current = true
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
    }
    setDisplayedText(text)
    setIsComplete(true)
  }

  // Build combined className
  const combinedClassName = [
    "inline-block",
    classNameProp,
  ]
    .filter(Boolean)
    .join(" ")

  if (!text) {
    return <span aria-label=""/>
  }

  return (
    <span className={combinedClassName} style={style} aria-label={text}>
      {isComplete ? (
        <span>{text}</span>
      ) : (
        displayedText
      )}
      {isComplete ? null : (
        <span onClick={handleSkip} className="ml-1 text-xs text-gray-500 cursor-pointer">
          Skip
        </span>
      )}
    </span>
  )
}