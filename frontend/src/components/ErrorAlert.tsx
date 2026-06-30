import React from 'react';

interface ErrorAlertProps {
  message: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ message }) => (
  <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-6">{message}</div>
);
