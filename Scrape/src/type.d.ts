// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Request } from 'express';
import User from '~/models/Schemas/User.schema';
import { TokenPayload } from './models/requests/user.request';
import Tweet from './models/Schemas/Tweet.schema';
declare module 'express' {
    interface Request {
        user?: User;
        decoded_authorization?: TokenPayload;
        decoded_refresh_token?: TokenPayload;
        decoded_email_verify_token?: TokenPayload;
        decoded_forgot_password_token?: TokenPayload;
        tweet?: Tweet;
    }
}