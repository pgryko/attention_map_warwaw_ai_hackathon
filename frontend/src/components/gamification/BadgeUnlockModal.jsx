import { useEffect, useState } from "react";
import { Modal, ModalHeader, ModalFooter } from "../ui/Modal";
import { Button } from "../ui/Button";
import { cn } from "../../lib/utils";

export function BadgeUnlockModal({ badge, isOpen, onClose }) {
  const [showConfetti, setShowConfetti] = useState(false);
  const [showBadge, setShowBadge] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Stagger animations
      setShowConfetti(true);
      const timer = setTimeout(() => setShowBadge(true), 200);
      return () => clearTimeout(timer);
    } else {
      setShowConfetti(false);
      setShowBadge(false);
    }
  }, [isOpen]);

  if (!badge) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="text-center">
      {/* Confetti background */}
      {showConfetti && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              className="confetti-piece"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 0.5}s`,
                backgroundColor: [
                  "#f59e0b",
                  "#10b981",
                  "#3b82f6",
                  "#8b5cf6",
                  "#ec4899",
                ][i % 5],
              }}
            />
          ))}
        </div>
      )}

      <ModalHeader onClose={onClose}>
        <span className="text-2xl">🎉</span> Badge Unlocked!
      </ModalHeader>

      <div className="py-6">
        {/* Badge icon with animation */}
        <div
          className={cn(
            "mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full",
            "bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg",
            "transition-all duration-500",
            showBadge ? "scale-100 opacity-100" : "scale-50 opacity-0",
          )}
        >
          <span className="text-5xl">{badge.icon || "🏆"}</span>
        </div>

        {/* Badge name */}
        <h3
          className={cn(
            "mb-2 text-xl font-bold text-gray-900 dark:text-white",
            "transition-all duration-500 delay-100",
            showBadge ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
          )}
        >
          {badge.name}
        </h3>

        {/* Badge description */}
        <p
          className={cn(
            "text-gray-600 dark:text-gray-400",
            "transition-all duration-500 delay-200",
            showBadge ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
          )}
        >
          {badge.description}
        </p>

        {/* Points earned */}
        {badge.points && (
          <div
            className={cn(
              "mt-4 inline-flex items-center gap-2 rounded-full bg-emerald-100 px-4 py-2 dark:bg-emerald-900/30",
              "transition-all duration-500 delay-300",
              showBadge ? "scale-100 opacity-100" : "scale-75 opacity-0",
            )}
          >
            <span className="font-bold text-emerald-600 dark:text-emerald-400">
              +{badge.points}
            </span>
            <span className="text-sm text-emerald-700 dark:text-emerald-300">
              reputation points
            </span>
          </div>
        )}
      </div>

      <ModalFooter className="justify-center">
        <Button onClick={onClose}>Awesome!</Button>
      </ModalFooter>

      {/* Inline styles for confetti animation */}
      <style>{`
        .confetti-piece {
          position: absolute;
          width: 10px;
          height: 10px;
          top: -10px;
          opacity: 0;
          animation: confetti-fall 3s ease-out forwards;
        }

        @keyframes confetti-fall {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(400px) rotate(720deg);
            opacity: 0;
          }
        }
      `}</style>
    </Modal>
  );
}

// Hook to manage badge unlock notifications
export function useBadgeUnlock() {
  const [pendingBadge, setPendingBadge] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  const showBadgeUnlock = (badge) => {
    setPendingBadge(badge);
    setIsOpen(true);
  };

  const closeBadgeUnlock = () => {
    setIsOpen(false);
    // Delay clearing the badge to allow close animation
    setTimeout(() => setPendingBadge(null), 300);
  };

  return {
    pendingBadge,
    isOpen,
    showBadgeUnlock,
    closeBadgeUnlock,
  };
}
