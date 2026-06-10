import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { NextConfig } from 'next'
import { parseChangelog } from './src/lib/release'

const projectRoot = join(dirname(fileURLToPath(import.meta.url)), '..')

function readAppVersion() {
    try {
        const version = readFileSync(join(projectRoot, 'VERSION'), 'utf-8').trim()
        return version || '0.0.0'
    } catch {
        return '0.0.0'
    }
}

const appVersion = process.env.NEXT_PUBLIC_APP_VERSION || readAppVersion()
const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
let appReleases = '[]'
try {
    appReleases = JSON.stringify(parseChangelog(readFileSync(join(projectRoot, 'CHANGELOG.md'), 'utf-8')))
} catch {}

const nextConfig: NextConfig = {
    allowedDevOrigins: ['127.0.0.1'],
    env: {
        NEXT_PUBLIC_APP_VERSION: appVersion,
        NEXT_PUBLIC_APP_RELEASES: appReleases,
    },
    output: 'export',
    trailingSlash: true,
    images: {
        unoptimized: true,
    },
    typescript: {
        ignoreBuildErrors: true,
    },
}

if (process.env.NODE_ENV === 'development') {
    nextConfig.rewrites = async () => [
        {
            source: '/images/:path*',
            destination: `${backendUrl}/images/:path*`,
        },
        {
            source: '/image-thumbnails/:path*',
            destination: `${backendUrl}/image-thumbnails/:path*`,
        },
    ]
}

export default nextConfig
