import jwt from 'jsonwebtoken';

export interface DecodedToken {
  user: {
    user_id: string;
    email: string;
    [key: string]: any;
  };
  job?: {
    job_id: number;
    [key: string]: any;
  };
  [key: string]: any;
}

export function verifyToken(token: string): DecodedToken {
  const secretKey = process.env.JWT_SECRET_KEY;

  if (!secretKey) {
    throw new Error('JWT_SECRET_KEY is not defined');
  }

  try {
    const decoded = jwt.verify(token, secretKey) as DecodedToken;
    
    if (!decoded.user || !decoded.user.user_id || !decoded.user.email) {
      throw new Error('Invalid token payload: missing user_id or email');
    }

    return decoded;
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new Error('Token has expired');
    } else if (error instanceof jwt.JsonWebTokenError) {
      throw new Error('Invalid token');
    }
    throw error;
  }
}
