import React from 'react';
import { motion } from 'framer-motion';
import { Shield, User, Calendar, Hash, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

interface ExtractedData {
  name?: string;
  dob?: string;
  id_number?: string;
  [key: string]: any;
}

interface VerificationResult {
  extracted: ExtractedData;
  trust_score: number;
  summary: string;
}

interface ResultCardProps {
  result: VerificationResult;
}

const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
  const { extracted, trust_score, summary } = result;

  const getTrustScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 50) return 'warning';
    return 'destructive';
  };

  const getTrustScoreIcon = (score: number) => {
    if (score >= 80) return CheckCircle;
    if (score >= 50) return AlertTriangle;
    return XCircle;
  };

  const getTrustScoreLabel = (score: number) => {
    if (score >= 80) return 'High Trust';
    if (score >= 50) return 'Medium Trust';
    return 'Low Trust';
  };

  const trustScoreColor = getTrustScoreColor(trust_score);
  const TrustIcon = getTrustScoreIcon(trust_score);
  const trustLabel = getTrustScoreLabel(trust_score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Trust Score Card */}
      <Card className="shadow-medium">
        <CardHeader className="text-center pb-6">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Shield className="w-6 h-6 text-primary" />
            <CardTitle className="text-xl">Verification Result</CardTitle>
          </div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="space-y-4"
          >
            <div className="relative inline-block">
              <div className="text-4xl font-bold text-primary mb-2">
                {trust_score}%
              </div>
              <Badge 
                variant={trustScoreColor as any}
                className="flex items-center space-x-1 px-3 py-1"
              >
                <TrustIcon className="w-4 h-4" />
                <span>{trustLabel}</span>
              </Badge>
            </div>

            <div className="w-full max-w-xs mx-auto space-y-2">
              <Progress 
                value={trust_score} 
                className={`h-3 ${
                  trustScoreColor === 'success' ? 'bg-success/20' :
                  trustScoreColor === 'warning' ? 'bg-warning/20' : 'bg-destructive/20'
                }`}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0%</span>
                <span>100%</span>
              </div>
            </div>
          </motion.div>
        </CardHeader>
      </Card>

      {/* Extracted Information Card */}
      <Card className="shadow-medium">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <User className="w-5 h-5 text-primary" />
            <span>Extracted Information</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="grid gap-4"
          >
            {extracted.name && (
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <User className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Full Name</span>
                </div>
                <span className="font-semibold">{extracted.name}</span>
              </div>
            )}

            {extracted.dob && (
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Date of Birth</span>
                </div>
                <span className="font-semibold">{extracted.dob}</span>
              </div>
            )}

            {extracted.id_number && (
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Hash className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">ID Number</span>
                </div>
                <span className="font-semibold font-mono">{extracted.id_number}</span>
              </div>
            )}

            {/* Additional fields */}
            {Object.entries(extracted)
              .filter(([key]) => !['name', 'dob', 'id_number'].includes(key))
              .map(([key, value]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm font-medium capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-semibold">{String(value)}</span>
                </div>
              ))}
          </motion.div>
        </CardContent>
      </Card>

      {/* Compliance Summary Card */}
      <Card className="shadow-medium">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-primary" />
            <span>Compliance Summary</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className={`
              p-4 rounded-lg border-l-4 
              ${trustScoreColor === 'success' 
                ? 'bg-success/10 border-l-success text-success-foreground' 
                : trustScoreColor === 'warning'
                  ? 'bg-warning/10 border-l-warning text-warning-foreground'
                  : 'bg-destructive/10 border-l-destructive text-destructive-foreground'
              }
            `}
          >
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {summary}
            </p>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ResultCard;