package dev.beevisual.module;

import dev.beevisual.setting.Setting;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

import java.util.ArrayList;
import java.util.List;

public abstract class Module {
    public final String name;
    public final String description;
    public final Category category;
    public final List<Setting> settings = new ArrayList<>();
    protected final MinecraftClient mc = MinecraftClient.getInstance();
    private boolean enabled;

    protected Module(String name, String description, Category category) {
        this.name = name;
        this.description = description;
        this.category = category;
    }

    protected Setting bool(String n, boolean def) {
        Setting s = Setting.ofBool(n, def);
        settings.add(s);
        return s;
    }

    protected Setting num(String n, double def, double min, double max, double step) {
        Setting s = Setting.ofNumber(n, def, min, max, step);
        settings.add(s);
        return s;
    }

    protected Setting mode(String n, int def, String... modes) {
        Setting s = Setting.ofMode(n, def, modes);
        settings.add(s);
        return s;
    }

    public boolean isEnabled() { return enabled; }

    public void setEnabled(boolean value) {
        if (value == enabled) return;
        enabled = value;
        if (value) onEnable();
        else onDisable();
    }

    public void toggle() { setEnabled(!enabled); }

    /** Used when loading config / after a crash: no callbacks. */
    public void forceEnabled(boolean value) { enabled = value; }

    public void onEnable() {}
    public void onDisable() {}
    public void onTick() {}
    public void onHud(DrawContext ctx, int width, int height) {}
}
