import { SignJWT, jwtVerify, type JWTPayload } from "jose";
import type { JwtPayload } from "./types";

const ALGORITHM = "HS256";
const TOKEN_EXPIRY = "24h";

/** Encode the JWT_SECRET string into a CryptoKey usable by jose. */
function getSecretKey(secret: string): Uint8Array {
  return new TextEncoder().encode(secret);
}

/** Sign a new JWT for the given user. */
export async function signToken(
  payload: { sub: string; email: string; role: string },
  secret: string,
): Promise<string> {
  return new SignJWT({ ...payload } as unknown as JWTPayload)
    .setProtectedHeader({ alg: ALGORITHM })
    .setIssuedAt()
    .setExpirationTime(TOKEN_EXPIRY)
    .sign(getSecretKey(secret));
}

/** Verify and decode a JWT token. Returns the payload or null. */
export async function verifyToken(
  token: string,
  secret: string,
): Promise<JwtPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getSecretKey(secret));
    return payload as unknown as JwtPayload;
  } catch {
    return null;
  }
}
