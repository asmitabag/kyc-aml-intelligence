// Only the status string is trusted; the actual value is always displayed to the user.
export const isKycComplete = (status) => /^(verified|approved|complete|completed|passed)$/i.test(String(status ?? ''));
