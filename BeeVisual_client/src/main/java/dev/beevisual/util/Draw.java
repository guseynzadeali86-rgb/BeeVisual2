package dev.beevisual.util;

import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;

/** Small drawing helpers (rounded rectangles, gradients) built on DrawContext.fill. */
public final class Draw {
    private Draw() {}

    public static int lerp(int a, int b, float t) {
        int aa = (int) (((a >>> 24) & 255) * (1 - t) + ((b >>> 24) & 255) * t);
        int ar = (int) (((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
        int ag = (int) (((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
        int ab = (int) ((a & 255) * (1 - t) + (b & 255) * t);
        return (aa << 24) | (ar << 16) | (ag << 8) | ab;
    }

    public static void rect(DrawContext c, int x, int y, int w, int h, int color) {
        c.fill(x, y, x + w, y + h, color);
    }

    private static int inset(int r, int i) {
        double d = r - i - 0.5;
        return (int) Math.round(r - Math.sqrt(Math.max(0, r * r - d * d)));
    }

    public static void round(DrawContext c, int x, int y, int w, int h, int r, int color) {
        r = Math.max(0, Math.min(r, Math.min(w, h) / 2));
        if (r == 0) {
            rect(c, x, y, w, h, color);
            return;
        }
        c.fill(x, y + r, x + w, y + h - r, color);
        for (int i = 0; i < r; i++) {
            int in = inset(r, i);
            c.fill(x + in, y + i, x + w - in, y + i + 1, color);
            c.fill(x + in, y + h - 1 - i, x + w - in, y + h - i, color);
        }
    }

    public static void gradH(DrawContext c, int x, int y, int w, int h, int c1, int c2) {
        for (int i = 0; i < w; i++) {
            c.fill(x + i, y, x + i + 1, y + h, lerp(c1, c2, w <= 1 ? 0f : (float) i / (w - 1)));
        }
    }

    public static void roundGradH(DrawContext c, int x, int y, int w, int h, int r, int c1, int c2) {
        r = Math.max(0, Math.min(r, Math.min(w, h) / 2));
        for (int i = 0; i < w; i++) {
            int trim = 0;
            if (i < r) trim = inset(r, i);
            else if (i >= w - r) trim = inset(r, w - 1 - i);
            c.fill(x + i, y + trim, x + i + 1, y + h - trim, lerp(c1, c2, w <= 1 ? 0f : (float) i / (w - 1)));
        }
    }

    public static void gradText(DrawContext c, TextRenderer tr, String s, int x, int y, int c1, int c2) {
        int cx = x;
        int n = s.length();
        for (int i = 0; i < n; i++) {
            String ch = s.substring(i, i + 1);
            c.drawTextWithShadow(tr, ch, cx, y, lerp(c1, c2, n <= 1 ? 0f : (float) i / (n - 1)));
            cx += tr.getWidth(ch);
        }
    }
}
