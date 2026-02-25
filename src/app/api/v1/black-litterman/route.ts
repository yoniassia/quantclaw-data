import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Black-Litterman Allocation API
 * Phase 36: Combine market equilibrium with investor views for portfolio construction
 */

const MODULES_DIR = path.join(process.cwd(), 'modules');
const BL_MODULE = path.join(MODULES_DIR, 'black_litterman.py');

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const action = searchParams.get('action') || 'help';
    
    let command: string;
    
    switch (action) {
      case 'black-litterman': {
        const tickers = searchParams.get('tickers');
        const views = searchParams.get('views');
        const confidence = searchParams.get('confidence') || '0.25';
        const period = searchParams.get('period') || '1y';
        
        if (!tickers) {
          return NextResponse.json({
            error: 'Missing required parameter: tickers (comma-separated)'
          }, { status: 400 });
        }
        
        command = `python3 ${BL_MODULE} black-litterman --tickers ${tickers} --confidence ${confidence} --period ${period}`;
        
        if (views) {
          command += ` --views ${views}`;
        }
        
        break;
      }
      
      case 'equilibrium-returns': {
        const tickers = searchParams.get('tickers');
        const period = searchParams.get('period') || '1y';
        
        if (!tickers) {
          return NextResponse.json({
            error: 'Missing required parameter: tickers'
          }, { status: 400 });
        }
        
        command = `python3 ${BL_MODULE} equilibrium-returns --tickers ${tickers} --period ${period}`;
        break;
      }
      
      case 'portfolio-optimize': {
        const tickers = searchParams.get('tickers');
        const targetReturn = searchParams.get('target-return');
        const allowShort = searchParams.get('allow-short') === 'true';
        const period = searchParams.get('period') || '1y';
        
        if (!tickers) {
          return NextResponse.json({
            error: 'Missing required parameter: tickers'
          }, { status: 400 });
        }
        
        command = `python3 ${BL_MODULE} portfolio-optimize --tickers ${tickers} --period ${period}`;
        
        if (targetReturn) {
          command += ` --target-return ${targetReturn}`;
        }
        
        if (allowShort) {
          command += ` --allow-short`;
        }
        
        break;
      }
      
      case 'help':
      default: {
        return NextResponse.json({
          service: 'Black-Litterman Allocation',
          phase: 36,
          description: 'Combine market equilibrium with investor views for portfolio construction',
          endpoints: {
            'black-litterman': {
              description: 'Full Black-Litterman model with investor views',
              params: {
                tickers: 'Comma-separated ticker symbols (required)',
                views: 'Views as TICKER:RETURN,... (e.g., AAPL:0.15,MSFT:0.10)',
                confidence: 'View confidence 0-1 (default: 0.25)',
                period: 'Historical data period (default: 1y)'
              },
              example: '/api/v1/black-litterman?action=black-litterman&tickers=AAPL,MSFT,GOOGL&views=AAPL:0.20,GOOGL:0.12'
            },
            'equilibrium-returns': {
              description: 'Derive implied equilibrium returns from market cap weights',
              params: {
                tickers: 'Comma-separated ticker symbols (required)',
                period: 'Historical data period (default: 1y)'
              },
              example: '/api/v1/black-litterman?action=equilibrium-returns&tickers=SPY,QQQ,IWM'
            },
            'portfolio-optimize': {
              description: 'Mean-variance optimization (max Sharpe ratio or target return)',
              params: {
                tickers: 'Comma-separated ticker symbols (required)',
                'target-return': 'Target annual return (optional, default: max Sharpe)',
                'allow-short': 'Allow short positions (default: false)',
                period: 'Historical data period (default: 1y)'
              },
              example: '/api/v1/black-litterman?action=portfolio-optimize&tickers=AAPL,MSFT,GOOGL&target-return=0.15'
            }
          },
          theory: {
            'Reverse Optimization': 'Derive equilibrium returns π = δΣw from market cap weights',
            'Black-Litterman Formula': 'E[R] = [(τΣ)⁻¹ + P\'Ω⁻¹P]⁻¹[(τΣ)⁻¹π + P\'Ω⁻¹Q]',
            'Posterior Covariance': 'Σ_post = Σ + M where M is precision matrix',
            'Mean-Variance Optimization': 'Maximize Sharpe ratio or achieve target return with minimum variance'
          },
          references: [
            'Black, F. and Litterman, R. (1992) "Global Portfolio Optimization"',
            'He, G. and Litterman, R. (1999) "The Intuition Behind Black-Litterman Model Portfolios"'
          ],
          parameters: {
            tau: 'Uncertainty scalar (default: 0.025)',
            delta: 'Risk aversion coefficient (default: 2.5)',
            omega: 'View uncertainty matrix (diagonal assumption)'
          }
        });
      }
    }
    
    // Execute Python module
    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 90000, // 90 second timeout for data fetching
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Python stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({
        error: 'Failed to parse Python output',
        raw: stdout,
        stderr: stderr
      }, { status: 500 });
    }
    
  } catch (error: any) {
    console.error('Black-Litterman API error:', error);
    return NextResponse.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, { status: 500 });
  }
}
