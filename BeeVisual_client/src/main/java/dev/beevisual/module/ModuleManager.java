package dev.beevisual.module;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.beevisual.BeeVisual;
import dev.beevisual.setting.Setting;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.gui.DrawContext;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ModuleManager {
    public static final List<Module> ALL = new ArrayList<>();
    public static Modules.WeatherControl WEATHER;

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private ModuleManager() {}

    private static Path path() {
        return FabricLoader.getInstance().getConfigDir().resolve("beevisual.json");
    }

    public static void init() {
        ALL.clear();
        // HUD
        ALL.add(new Modules.Watermark());
        ALL.add(new Modules.FeatureList());
        ALL.add(new Modules.Speedometer());
        ALL.add(new Modules.SessionInfo());
        ALL.add(new Modules.TargetHud());
        ALL.add(new Modules.InventoryPreview());
        ALL.add(new Modules.Cooldowns());
        ALL.add(new Modules.Keystrokes());
        ALL.add(new Modules.Coords());
        ALL.add(new Modules.PotionHud());
        ALL.add(new Modules.ArmorHud());
        // Render
        ALL.add(new Modules.Trails());
        ALL.add(new Modules.JumpCircles());
        ALL.add(new Modules.ChinaHat());
        ALL.add(new Modules.FullBright());
        ALL.add(new Modules.Zoom());
        // World
        WEATHER = new Modules.WeatherControl();
        ALL.add(WEATHER);
        ALL.add(new Modules.Ambience());
        ALL.add(new Modules.SnowGround());
    }

    public static List<Category> categories() {
        List<Category> out = new ArrayList<>();
        for (Category c : Category.values()) if (!in(c).isEmpty()) out.add(c);
        return out;
    }

    public static List<Module> in(Category c) {
        List<Module> out = new ArrayList<>();
        for (Module m : ALL) if (m.category == c) out.add(m);
        return out;
    }

    public static void tick() {
        for (Module m : ALL) {
            if (!m.isEnabled()) continue;
            try {
                m.onTick();
            } catch (Throwable t) {
                fail(m, t);
            }
        }
    }

    public static void hud(DrawContext ctx, int w, int h) {
        for (Module m : ALL) {
            if (!m.isEnabled()) continue;
            try {
                m.onHud(ctx, w, h);
            } catch (Throwable t) {
                fail(m, t);
            }
        }
    }

    private static void fail(Module m, Throwable t) {
        BeeVisual.LOG.error("Module {} crashed and was disabled", m.name, t);
        m.forceEnabled(false);
    }

    // ------------------------------------------------------------ config
    public static void save() {
        try {
            JsonObject root = new JsonObject();
            for (Module m : ALL) {
                JsonObject o = new JsonObject();
                o.addProperty("enabled", m.isEnabled());
                for (Setting s : m.settings) {
                    switch (s.type) {
                        case BOOL -> o.addProperty(s.name, s.bool);
                        case NUMBER -> o.addProperty(s.name, s.value);
                        default -> o.addProperty(s.name, s.index);
                    }
                }
                root.add(m.name, o);
            }
            Files.writeString(path(), GSON.toJson(root), StandardCharsets.UTF_8);
        } catch (Exception e) {
            BeeVisual.LOG.warn("Could not save config", e);
        }
    }

    public static void load() {
        try {
            Path p = path();
            if (!Files.exists(p)) return;
            JsonObject root = JsonParser.parseString(Files.readString(p, StandardCharsets.UTF_8)).getAsJsonObject();
            for (Module m : ALL) {
                if (!root.has(m.name)) continue;
                JsonObject o = root.getAsJsonObject(m.name);
                if (o.has("enabled")) m.forceEnabled(o.get("enabled").getAsBoolean());
                for (Setting s : m.settings) {
                    if (!o.has(s.name)) continue;
                    JsonElement v = o.get(s.name);
                    switch (s.type) {
                        case BOOL -> s.bool = v.getAsBoolean();
                        case NUMBER -> s.value = Math.max(s.min, Math.min(s.max, v.getAsDouble()));
                        default -> s.index = Math.max(0, Math.min(s.modes.length - 1, v.getAsInt()));
                    }
                }
            }
        } catch (Exception e) {
            BeeVisual.LOG.warn("Could not load config (using defaults)", e);
        }
    }
}
