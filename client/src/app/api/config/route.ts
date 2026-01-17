import { NextResponse } from 'next/server';

export async function GET() {
    const botStartUrl =
        process.env.BOT_START_URL || 'http://localhost:7860/start';

    const botApiUrl = botStartUrl.replace(/\/start$/, '');
    const configUrl = `${botApiUrl}/config`;

    try {
        const response = await fetch(configUrl);

        if (!response.ok) {
            throw new Error(`Failed to fetch config from bot: ${response.statusText}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Failed to fetch bot config:', error);
        return NextResponse.json(
            {
                error: `Failed to fetch config: ${error}`,
            },
            { status: 500 }
        );
    }
}
