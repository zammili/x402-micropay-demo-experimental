import * as fs from 'fs';
import * as path from 'path';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  context?: any;
}

class Logger {
  private logLevel: string;
  private logDir: string;

  constructor(level: string = 'info') {
    this.logLevel = process.env.LOG_LEVEL || level;
    this.logDir = path.join(process.cwd(), 'logs');

    // Create logs directory if it doesn't exist
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  private getTimestamp(): string {
    return new Date().toISOString();
  }

  private formatMessage(level: string, message: string, context?: any): LogEntry {
    return {
      timestamp: this.getTimestamp(),
      level,
      message,
      context,
    };
  }

  private writeLog(entry: LogEntry): void {
    const logFile = path.join(this.logDir, `${new Date().toISOString().split('T')[0]}.log`);
    const logLine = JSON.stringify(entry) + '\n';
    fs.appendFileSync(logFile, logLine);
  }

  info(message: string, context?: any): void {
    const entry = this.formatMessage('INFO', message, context);
    console.log(`[${entry.timestamp}] INFO: ${message}`);
    this.writeLog(entry);
  }

  warn(message: string, context?: any): void {
    const entry = this.formatMessage('WARN', message, context);
    console.warn(`[${entry.timestamp}] WARN: ${message}`);
    this.writeLog(entry);
  }

  error(message: string, context?: any): void {
    const entry = this.formatMessage('ERROR', message, context);
    console.error(`[${entry.timestamp}] ERROR: ${message}`);
    this.writeLog(entry);
  }

  debug(message: string, context?: any): void {
    if (this.logLevel === 'debug') {
      const entry = this.formatMessage('DEBUG', message, context);
      console.log(`[${entry.timestamp}] DEBUG: ${message}`);
      this.writeLog(entry);
    }
  }
}

export const logger = new Logger();