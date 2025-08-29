import React from 'react';
import { motion } from 'framer-motion';
import { Check, Upload, Search, Shield, CheckCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface ProgressBarProps {
  currentStep: number;
  isLoading: boolean;
}

const steps = [
  { id: 1, title: 'Upload', description: 'Upload your documents', icon: Upload },
  { id: 2, title: 'Extract', description: 'Extracting information', icon: Search },
  { id: 3, title: 'Verify', description: 'Verifying identity', icon: Shield },
  { id: 4, title: 'Complete', description: 'Verification complete', icon: CheckCircle }
];

const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep, isLoading }) => {
  const progressPercentage = ((currentStep - 1) / (steps.length - 1)) * 100;

  return (
    <div className="w-full space-y-6">
      {/* Progress Line */}
      <div className="relative">
        <div className="flex justify-between items-center">
          {steps.map((step, index) => {
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            const IconComponent = step.icon;

            return (
              <div key={step.id} className="flex flex-col items-center z-10 relative">
                <motion.div
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300
                    ${isCompleted 
                      ? 'bg-success border-success text-success-foreground shadow-glow' 
                      : isActive 
                        ? 'bg-primary border-primary text-primary-foreground shadow-glow animate-pulse' 
                        : 'bg-muted border-border text-muted-foreground'
                    }
                  `}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1, type: 'spring', stiffness: 200 }}
                  whileHover={{ scale: 1.1 }}
                >
                  {isCompleted ? (
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: 'spring', stiffness: 300 }}
                    >
                      <Check className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <motion.div
                      animate={isActive && isLoading ? { 
                        rotate: 360,
                        transition: { duration: 2, repeat: Infinity, ease: 'linear' }
                      } : {}}
                    >
                      <IconComponent className="w-5 h-5" />
                    </motion.div>
                  )}
                </motion.div>

                <div className="mt-3 text-center">
                  <div className={`text-sm font-medium ${
                    isCompleted ? 'text-success' : isActive ? 'text-primary' : 'text-muted-foreground'
                  }`}>
                    {step.title}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 hidden sm:block">
                    {step.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Line Background */}
        <div className="absolute top-6 left-6 right-6 h-0.5 bg-border -z-10">
          <motion.div
            className="h-full bg-gradient-primary"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
          />
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{Math.round(progressPercentage)}%</span>
        </div>
        <Progress 
          value={progressPercentage} 
          className="h-2 bg-muted"
        />
      </div>

      {/* Current Step Info */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center p-4 bg-accent/20 rounded-lg border border-accent/30"
        >
          <div className="flex items-center justify-center space-x-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full"
            />
            <span className="text-sm font-medium">
              {steps.find(step => step.id === currentStep)?.description}...
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ProgressBar;