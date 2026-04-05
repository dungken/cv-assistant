import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Star, Send, X, AlertCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/Dialog';
import { Button } from '../ui/Button';
import { feedbackApi } from '../../services/api';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  itemId?: string;
}

export default function FeedbackModal({ isOpen, onClose, itemId }: FeedbackModalProps) {
  const { t } = useTranslation();
  const [rating, setRating] = React.useState(0);
  const [hoverRating, setHoverRating] = React.useState(0);
  const [comment, setComment] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isSuccess, setIsSuccess] = React.useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;
    setIsSubmitting(true);
    try {
      await feedbackApi.create({
        itemId,
        type: 'CV_Rating',
        rating,
        comment
      });
      setIsSuccess(true);
      setTimeout(() => {
        onClose();
        setIsSuccess(false);
        setRating(0);
        setComment('');
      }, 2000);
    } catch (error) {
      console.error('Feedback failed', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-canvas-dark/95 backdrop-blur-2xl border-white/10 shadow-2xl rounded-3xl p-8 overflow-hidden">
        <DialogHeader className="mb-6">
          <DialogTitle className="text-2xl font-bold font-outfit text-center bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent italic">
            {t('feedback.title')}
          </DialogTitle>
        </DialogHeader>

        {isSuccess ? (
          <div className="flex flex-col items-center justify-center py-10 animate-in fade-in zoom-in-95 duration-500 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-4 border border-emerald-500/30">
              <Send className="w-8 h-8 text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Thank you!</h3>
            <p className="text-sm text-text-secondary">Your feedback helps us improve.</p>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm text-text-secondary font-medium tracking-tight">
                {t('feedback.question')}
              </p>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setRating(star)}
                    className="group relative focus:outline-none transition-transform active:scale-90"
                  >
                    <Star
                      className={`w-10 h-10 transition-all duration-300 ${
                        (hoverRating || rating) >= star
                          ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_12px_rgba(251,191,36,0.5)]'
                          : 'text-white/10 hover:text-white/30'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={t('feedback.comment_placeholder')}
                className="w-full h-32 bg-white/5 border border-white/10 rounded-2xl p-4 text-sm text-white placeholder:text-text-secondary/30 focus:outline-none focus:ring-2 focus:ring-accent-primary/30 focus:border-accent-primary/30 transition-all resize-none font-medium"
              />
              <div className="flex items-center gap-2 px-1 py-1 bg-accent-primary/5 rounded-xl border border-accent-primary/10">
                <AlertCircle className="w-3 h-3 text-accent-primary ml-2" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-accent-primary/60">
                   {t('feedback.correction_tip')}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
               <Button variant="ghost" onClick={onClose} className="flex-1 h-12 rounded-2xl border border-white/5 hover:bg-white/5">
                 Maybe later
               </Button>
               <Button
                disabled={rating === 0 || isSubmitting}
                onClick={handleSubmit}
                className="flex-1 h-12 rounded-2xl bg-accent-primary hover:bg-accent-primary/90 text-white shadow-lg shadow-accent-primary/25 relative overflow-hidden group"
               >
                 {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                 ) : (
                   <span className="font-bold tracking-tight">Submit Feedback</span>
                 )}
               </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
