package dev.beevisual.gui;

import dev.beevisual.Theme;
import dev.beevisual.module.Category;
import dev.beevisual.module.Module;
import dev.beevisual.module.ModuleManager;
import dev.beevisual.setting.Setting;
import dev.beevisual.util.Draw;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** BeeVisual ClickGUI: opens on Right Shift. LMB toggles a module, RMB opens its settings. */
public class ClickGuiScreen extends Screen {
    private static final int PW = 190, GAP = 12, HEADER = 26, ROW = 22, SROW = 18;

    private enum Kind { MODULE, BOOL, SLIDER, MODE }

    private record Hit(int x, int y, int w, int h, Module module, Setting setting, Kind kind) {
        boolean contains(double mx, double my) {
            return mx >= x && mx < x + w && my >= y && my < y + h;
        }
    }

    private record PanelRect(int x, int y, int w, int h, Category cat, int maxScroll) {}

    private final Map<Category, Integer> scroll = new EnumMap<>(Category.class);
    private final Set<Module> expanded = new HashSet<>();
    private final List<Hit> hits = new ArrayList<>();
    private final List<PanelRect> panels = new ArrayList<>();
    private Hit dragging;

    public ClickGuiScreen() {
        super(Text.literal("BeeVisual"));
    }

    private TextRenderer tr() {
        return MinecraftClient.getInstance().textRenderer;
    }

    @Override
    public boolean shouldPause() {
        return false;
    }

    @Override
    public void removed() {
        ModuleManager.save();
    }

    @Override
    public void render(DrawContext ctx, int mouseX, int mouseY, float delta) {
        hits.clear();
        panels.clear();
        TextRenderer tr = tr();
        ctx.fill(0, 0, width, height, 0xAA000000);

        List<Category> cats = ModuleManager.categories();
        int n = cats.size();
        int total = n * PW + (n - 1) * GAP;
        int x0 = (width - total) / 2;
        int y0 = 34;

        // title
        ctx.getMatrices().push();
        ctx.getMatrices().translate(width / 2f - tr.getWidth("BeeVisual"), 8f, 0f);
        ctx.getMatrices().scale(2f, 2f, 1f);
        Draw.gradText(ctx, tr, "BeeVisual", 0, 0, Theme.A1, Theme.A2);
        ctx.getMatrices().pop();

        for (int i = 0; i < n; i++) {
            Category cat = cats.get(i);
            int px = x0 + i * (PW + GAP);
            List<Module> mods = ModuleManager.in(cat);

            int content = 0;
            for (Module m : mods) content += ROW + 2 + (expanded.contains(m) ? m.settings.size() * SROW + 4 : 0);
            int maxH = height - y0 - 34;
            int ph = Math.min(HEADER + content + 6, maxH);
            int viewTop = y0 + HEADER + 3;
            int viewH = ph - HEADER - 6;
            int maxScroll = Math.max(0, content - viewH);
            int sc = Math.max(0, Math.min(maxScroll, scroll.getOrDefault(cat, 0)));
            scroll.put(cat, sc);
            panels.add(new PanelRect(px, y0, PW, ph, cat, maxScroll));

            Draw.round(ctx, px, y0, PW, ph, 6, Theme.PANEL);
            Draw.roundGradH(ctx, px, y0, PW, HEADER, 6, 0xFF2A2314, 0xFF1A160D);
            Draw.gradH(ctx, px + 8, y0 + HEADER - 2, PW - 16, 2, Theme.A1, Theme.A2);
            ctx.drawTextWithShadow(tr, cat.title, px + 10, y0 + 9, Theme.CREAM);
            String cnt = String.valueOf(mods.size());
            ctx.drawTextWithShadow(tr, cnt, px + PW - 10 - tr.getWidth(cnt), y0 + 9, Theme.GRAY);

            ctx.enableScissor(px, viewTop, px + PW, viewTop + viewH);
            int cy = viewTop - sc;
            int rx = px + 5, rw = PW - 10;
            for (Module m : mods) {
                boolean on = m.isEnabled();
                if (on) Draw.roundGradH(ctx, rx, cy, rw, ROW, 4, Theme.A1, Theme.A2);
                else Draw.round(ctx, rx, cy, rw, ROW, 4, Theme.ROW);
                int tc = on ? Theme.INK : Theme.CREAM;
                ctx.drawText(tr, m.name, rx + 8, cy + (ROW - 8) / 2, tc, false);
                if (!m.settings.isEmpty()) {
                    String ind = expanded.contains(m) ? "v" : ">";
                    ctx.drawText(tr, ind, rx + rw - 12, cy + (ROW - 8) / 2, on ? Theme.INK : Theme.GRAY, false);
                }
                addHit(rx, cy, rw, ROW, viewTop, viewTop + viewH, m, null, Kind.MODULE);
                cy += ROW;

                if (expanded.contains(m)) {
                    int boxH = m.settings.size() * SROW + 4;
                    Draw.round(ctx, rx + 3, cy, rw - 6, boxH, 4, 0xFF0C0B08);
                    int sy = cy + 2;
                    for (Setting s : m.settings) {
                        drawSetting(ctx, tr, s, rx + 3, sy, rw - 6);
                        Kind k = s.type == Setting.Type.BOOL ? Kind.BOOL : s.type == Setting.Type.NUMBER ? Kind.SLIDER : Kind.MODE;
                        addHit(rx + 3, sy, rw - 6, SROW, viewTop, viewTop + viewH, m, s, k);
                        sy += SROW;
                    }
                    cy += boxH;
                }
                cy += 2;
            }
            ctx.disableScissor();
        }

        String hint = "Правый Shift — закрыть   •   ЛКМ — вкл/выкл   •   ПКМ — настройки   •   колесо — прокрутка";
        ctx.drawCenteredTextWithShadow(tr, hint, width / 2, height - 20, Theme.GRAY);
    }

    private void drawSetting(DrawContext ctx, TextRenderer tr, Setting s, int x, int y, int w) {
        ctx.drawText(tr, s.name, x + 5, y + 2, Theme.CREAM, false);
        switch (s.type) {
            case BOOL -> {
                int bx = x + w - 16;
                Draw.round(ctx, bx, y + 3, 9, 9, 2, s.bool ? Theme.A1 : Theme.TRACK);
            }
            case NUMBER -> {
                String v = s.display();
                ctx.drawText(tr, v, x + w - 5 - tr.getWidth(v), y + 2, Theme.A1, false);
                int tw = w - 10;
                Draw.rect(ctx, x + 5, y + SROW - 5, tw, 2, Theme.TRACK);
                double f = (s.value - s.min) / (s.max - s.min);
                int fw = (int) (tw * Math.max(0, Math.min(1, f)));
                if (fw > 0) Draw.gradH(ctx, x + 5, y + SROW - 5, fw, 2, Theme.A1, Theme.A2);
            }
            default -> {
                String v = s.display();
                ctx.drawText(tr, v, x + w - 5 - tr.getWidth(v), y + 2, Theme.A1, false);
            }
        }
    }

    private void addHit(int x, int y, int w, int h, int clipTop, int clipBottom, Module m, Setting s, Kind k) {
        int y1 = Math.max(y, clipTop);
        int y2 = Math.min(y + h, clipBottom);
        if (y2 <= y1) return;
        hits.add(new Hit(x, y1, w, y2 - y1, m, s, k));
    }

    private void sliderTo(Hit h, double mx) {
        Setting s = h.setting();
        double tx = h.x() + 5;
        double tw = h.w() - 10;
        double f = Math.max(0, Math.min(1, (mx - tx) / tw));
        double v = s.min + f * (s.max - s.min);
        if (s.step > 0) v = Math.round(v / s.step) * s.step;
        s.value = Math.max(s.min, Math.min(s.max, v));
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        for (int i = hits.size() - 1; i >= 0; i--) {
            Hit h = hits.get(i);
            if (!h.contains(mx, my)) continue;
            switch (h.kind()) {
                case MODULE -> {
                    if (button == 0) h.module().toggle();
                    else if (button == 1 && !h.module().settings.isEmpty()) {
                        if (!expanded.remove(h.module())) expanded.add(h.module());
                    }
                }
                case BOOL -> {
                    if (button == 0) h.setting().bool = !h.setting().bool;
                }
                case MODE -> {
                    if (button == 0) h.setting().next(1);
                    else if (button == 1) h.setting().next(-1);
                }
                case SLIDER -> {
                    if (button == 0) {
                        dragging = h;
                        sliderTo(h, mx);
                    }
                }
            }
            ModuleManager.save();
            return true;
        }
        return super.mouseClicked(mx, my, button);
    }

    @Override
    public boolean mouseDragged(double mx, double my, int button, double dx, double dy) {
        if (dragging != null && button == 0) {
            sliderTo(dragging, mx);
            return true;
        }
        return super.mouseDragged(mx, my, button, dx, dy);
    }

    @Override
    public boolean mouseReleased(double mx, double my, int button) {
        if (dragging != null) {
            dragging = null;
            ModuleManager.save();
        }
        return super.mouseReleased(mx, my, button);
    }

    @Override
    public boolean mouseScrolled(double mx, double my, double horizontal, double vertical) {
        for (PanelRect p : panels) {
            if (mx >= p.x() && mx < p.x() + p.w() && my >= p.y() && my < p.y() + p.h()) {
                int cur = scroll.getOrDefault(p.cat(), 0);
                scroll.put(p.cat(), Math.max(0, Math.min(p.maxScroll(), cur - (int) (vertical * 16))));
                return true;
            }
        }
        return super.mouseScrolled(mx, my, horizontal, vertical);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == GLFW.GLFW_KEY_RIGHT_SHIFT || keyCode == GLFW.GLFW_KEY_ESCAPE) {
            close();
            return true;
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }
}
