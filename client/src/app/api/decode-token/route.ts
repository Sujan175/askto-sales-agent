import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';

export async function POST(request: Request) {
  try {
    const { token } = await request.json();

    if (!token) {
      return NextResponse.json(
        { error: 'Token is required' },
        { status: 400 }
      );
    }

    const secretKey = process.env.JWT_SECRET_KEY;

    if (!secretKey) {
      console.error('JWT_SECRET_KEY is not defined');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }

    try {
      const decoded = jwt.verify(token, secretKey);
      return NextResponse.json({ decoded });
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        return NextResponse.json(
          { error: 'Token has expired' },
          { status: 401 }
        );
      } else if (error instanceof jwt.JsonWebTokenError) {
        return NextResponse.json(
          { error: 'Invalid token' },
          { status: 401 }
        );
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error('Error decoding token:', error);
    return NextResponse.json(
      { error: 'Failed to decode token' },
      { status: 500 }
    );
  }
}
