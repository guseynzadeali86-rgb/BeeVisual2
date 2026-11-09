package dev.beevisual.module;

import dev.beevisual.BeeVisual;
import dev.beevisual.Stats;
import dev.beevisual.Theme;
import dev.beevisual.setting.Setting;
import dev.beevisual.util.Draw;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.particle.ParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.math.Direction;
import net.minecraft.world.Heightmap;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

/** All BeeVisual modules. */
public final class Modules {
    private Modules() {}

    static final String[] PARTICLE_NAMES = {"Звёзды", "Искры", "Снежинки", "Огонь", "Синий огонь", "Сердечки"};

    static ParticleEffect particle(int i) {
        return switch (i) {
            case 1 -> ParticleTypes.ELECTRIC_SPARK;
            case 2 -> ParticleTypes.SNOWFLAKE;
            case 3 -> ParticleTypes.FLAME;
            case 4 -> ParticleTypes.SOUL_FIRE_FLAME;
            case 5 -> ParticleTypes.HAPPY_VILLAGER;
            default -> ParticleTypes.END_ROD;
        };
    }

    // ============================================================ HUD

    public static class Watermark extends Module {
        private final Setting showNick = bool("Ник", true);
        private final Setting showPing = bool("Пинг", true);

        public Watermark() {
            super("Watermark", "Логотип BeeVisual с ником и FPS", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            TextRenderer tr = mc.textRenderer;
            StringBuilder info = new StringBuilder(mc.getCurrentFps() + " FPS");
            if (showPing.getBool() && mc.getNetworkHandler() != null && mc.player != null) {
                PlayerListEntry e = mc.getNetworkHandler().getPlayerListEntry(mc.player.getUuid());
                if (e != null) info.append("  ").append(e.getLatency()).append(" ms");
            }
            if (showNick.getBool()) info.append("  ").append(mc.getSession().getUsername());
            String name = "BeeVisual";
            int bw = tr.getWidth(name) + tr.getWidth(info.toString()) + 22;
            Draw.round(c, 6, 6, bw, 16, 4, Theme.DARK);
            Draw.rect(c, 6, 9, 2, 10, Theme.A1);
            Draw.gradText(c, tr, name, 12, 10, Theme.A1, Theme.A2);
            c.drawTextWithShadow(tr, info.toString(), 12 + tr.getWidth(name) + 8, 10, Theme.GRAY);
        }
    }

    public static class Speedometer extends Module {
        public Speedometer() {
            super("Speedometer", "Скорость в блоках в секунду", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            TextRenderer tr = mc.textRenderer;
            String label = "Скорость ";
            String val = String.format(Locale.ROOT, "%.1f б/с", Stats.speed);
            int bw = tr.getWidth(label) + tr.getWidth(val) + 12;
            Draw.round(c, 6, 26, bw, 16, 4, Theme.DARK);
            c.drawTextWithShadow(tr, label, 11, 30, Theme.GRAY);
            c.drawTextWithShadow(tr, val, 11 + tr.getWidth(label), 30, Theme.A1);
        }
    }

    public static class SessionInfo extends Module {
        public SessionInfo() {
            super("SessionInfo", "Время в игре, убийства и смерти", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            TextRenderer tr = mc.textRenderer;
            long sec = (System.currentTimeMillis() - Stats.sessionStart) / 1000;
            String t = String.format(Locale.ROOT, "%02d:%02d:%02d", sec / 3600, (sec / 60) % 60, sec % 60);
            String l1 = "Сессия  " + t;
            String l2 = "Убийства " + Stats.kills + "   Смерти " + Stats.deaths;
            int bw = Math.max(tr.getWidth(l1), tr.getWidth(l2)) + 12;
            Draw.round(c, 6, 46, bw, 28, 4, Theme.DARK);
            c.drawTextWithShadow(tr, l1, 11, 50, Theme.CREAM);
            c.drawTextWithShadow(tr, l2, 11, 62, Theme.GRAY);
        }
    }

    public static class PotionHud extends Module {
        public PotionHud() {
            super("PotionHUD", "Активные эффекты и таймеры", Category.HUD);
        }

        private static String roman(int n) {
            return switch (n) {
                case 1 -> "I";
                case 2 -> "II";
                case 3 -> "III";
                case 4 -> "IV";
                case 5 -> "V";
                default -> String.valueOf(n);
            };
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            if (mc.player == null) return;
            TextRenderer tr = mc.textRenderer;
            int y = 80;
            for (StatusEffectInstance e : mc.player.getStatusEffects()) {
                String name = e.getEffectType().value().getName().getString() + " " + roman(e.getAmplifier() + 1);
                int d = e.getDuration();
                String time = d < 0 ? "∞" : String.format(Locale.ROOT, "%d:%02d", d / 1200, (d / 20) % 60);
                int bw = tr.getWidth(name) + tr.getWidth(time) + 22;
                Draw.round(c, 6, y, bw, 15, 4, Theme.DARK);
                c.drawTextWithShadow(tr, name, 11, y + 4, Theme.CREAM);
                c.drawTextWithShadow(tr, time, 11 + tr.getWidth(name) + 10, y + 4, d >= 0 && d < 200 ? 0xFFFF6A5A : Theme.A1);
                y += 17;
            }
        }
    }

    public static class TargetHud extends Module {
        public TargetHud() {
            super("TargetHUD", "Окно с ником и ХП цели при ударе", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            LivingEntity t = Stats.target;
            if (t == null || System.currentTimeMillis() - Stats.lastHit > 5000) return;
            TextRenderer tr = mc.textRenderer;
            int bx = w / 2 + 24, by = h / 2 + 24, bw = 150, bh = 38;
            String name = t.getName().getString();
            Draw.round(c, bx, by, bw, bh, 5, Theme.DARK);
            Draw.round(c, bx + 5, by + 5, 28, 28, 5, Theme.ROW);
            String letter = name.isEmpty() ? "?" : name.substring(0, 1).toUpperCase(Locale.ROOT);
            c.drawCenteredTextWithShadow(tr, letter, bx + 19, by + 15, Theme.A1);
            c.drawTextWithShadow(tr, name, bx + 39, by + 6, Theme.CREAM);
            float hp = Math.max(0f, t.getHealth());
            float max = Math.max(1f, t.getMaxHealth());
            float f = Math.min(1f, hp / max);
            int barW = bw - 46;
            Draw.round(c, bx + 39, by + 19, barW, 6, 3, 0xFF2A261C);
            int fw = (int) (barW * f);
            if (fw > 0) {
                int c1 = Draw.lerp(0xFFFF4040, Theme.A1, f);
                Draw.roundGradH(c, bx + 39, by + 19, fw, 6, 3, c1, Draw.lerp(0xFFFF6030, Theme.A2, f));
            }
            String hs = String.format(Locale.ROOT, "%.1f HP", hp + t.getAbsorptionAmount());
            c.drawTextWithShadow(tr, hs, bx + 39, by + 27, Theme.GRAY);
        }
    }

    public static class InventoryPreview extends Module {
        public InventoryPreview() {
            super("InventoryPreview", "Мини-инвентарь на экране без нажатия E", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            if (mc.player == null) return;
            int cell = 18;
            int bw = 9 * cell + 8, bh = 3 * cell + 8;
            int bx = w - bw - 6, by = h - bh - 6;
            Draw.round(c, bx, by, bw, bh, 5, Theme.DARK);
            for (int i = 0; i < 27; i++) {
                ItemStack st = mc.player.getInventory().getStack(9 + i);
                if (st.isEmpty()) continue;
                int x = bx + 4 + (i % 9) * cell + 1;
                int y = by + 4 + (i / 9) * cell + 1;
                c.drawItem(st, x, y);
                c.drawStackOverlay(mc.textRenderer, st, x, y);
            }
        }
    }

    public static class Cooldowns extends Module {
        private static final Item[] ITEMS = {Items.ENDER_PEARL, Items.CHORUS_FRUIT, Items.GOLDEN_APPLE, Items.ENCHANTED_GOLDEN_APPLE, Items.SHIELD};
        private final Map<Item, double[]> track = new HashMap<>(); // {startMillis, startProgress}

        public Cooldowns() {
            super("Cooldowns", "Таймеры перезарядки перлов, хорусов, яблок", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            if (mc.player == null) return;
            TextRenderer tr = mc.textRenderer;
            int x = w - 132, y = h / 2 + 30;
            long now = System.currentTimeMillis();
            for (Item item : ITEMS) {
                ItemStack st = new ItemStack(item);
                float p = mc.player.getItemCooldownManager().getCooldownProgress(st, 0f);
                if (p <= 0f) {
                    track.remove(item);
                    continue;
                }
                double[] tk = track.computeIfAbsent(item, k -> new double[]{now, p});
                String txt = "…";
                if (tk[1] - p > 0.01) {
                    double rem = (now - tk[0]) / 1000.0 * p / (tk[1] - p);
                    txt = String.format(Locale.ROOT, "%.1f с", rem);
                }
                Draw.round(c, x, y, 126, 20, 4, Theme.DARK);
                c.drawItem(st, x + 2, y + 2);
                c.drawTextWithShadow(tr, txt, x + 24, y + 3, Theme.CREAM);
                Draw.round(c, x + 24, y + 14, 96, 3, 1, 0xFF2A261C);
                int fw = (int) (96 * p);
                if (fw > 0) Draw.roundGradH(c, x + 24, y + 14, fw, 3, 1, Theme.A1, Theme.A2);
                y += 22;
            }
        }
    }

    public static class Keystrokes extends Module {
        private final ArrayDeque<Long> lmb = new ArrayDeque<>();
        private final ArrayDeque<Long> rmb = new ArrayDeque<>();
        private boolean lastA;
        private boolean lastU;

        public Keystrokes() {
            super("Keystrokes", "WASD, мышь и CPS", Category.HUD);
        }

        @Override
        public void onTick() {
            long now = System.currentTimeMillis();
            boolean a = mc.options.attackKey.isPressed();
            boolean u = mc.options.useKey.isPressed();
            if (a && !lastA) lmb.add(now);
            if (u && !lastU) rmb.add(now);
            lastA = a;
            lastU = u;
            while (!lmb.isEmpty() && now - lmb.peekFirst() > 1000) lmb.pollFirst();
            while (!rmb.isEmpty() && now - rmb.peekFirst() > 1000) rmb.pollFirst();
        }

        private void key(DrawContext c, int x, int y, int kw, int kh, String label, boolean on) {
            if (on) Draw.roundGradH(c, x, y, kw, kh, 4, Theme.A1, Theme.A2);
            else Draw.round(c, x, y, kw, kh, 4, Theme.DARK);
            TextRenderer tr = mc.textRenderer;
            c.drawText(tr, label, x + (kw - tr.getWidth(label)) / 2, y + (kh - 8) / 2 + 1, on ? Theme.INK : Theme.CREAM, false);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            int bx = 6, by = h / 2 - 8;
            key(c, bx + 22, by, 20, 20, "W", mc.options.forwardKey.isPressed());
            key(c, bx, by + 22, 20, 20, "A", mc.options.leftKey.isPressed());
            key(c, bx + 22, by + 22, 20, 20, "S", mc.options.backKey.isPressed());
            key(c, bx + 44, by + 22, 20, 20, "D", mc.options.rightKey.isPressed());
            key(c, bx, by + 44, 31, 20, "ЛКМ " + lmb.size(), mc.options.attackKey.isPressed());
            key(c, bx + 33, by + 44, 31, 20, "ПКМ " + rmb.size(), mc.options.useKey.isPressed());
        }
    }

    public static class Coords extends Module {
        public Coords() {
            super("Coords", "Координаты и направление", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            if (mc.player == null) return;
            TextRenderer tr = mc.textRenderer;
            Direction d = mc.player.getHorizontalFacing();
            String dir = switch (d) {
                case NORTH -> "Север";
                case SOUTH -> "Юг";
                case EAST -> "Восток";
                default -> "Запад";
            };
            String s = "XYZ  " + mc.player.getBlockX() + " / " + mc.player.getBlockY() + " / " + mc.player.getBlockZ() + "  " + dir;
            int bw = tr.getWidth(s) + 12;
            int y = h / 2 - 30;
            Draw.round(c, 6, y, bw, 16, 4, Theme.DARK);
            c.drawTextWithShadow(tr, s, 11, y + 4, Theme.CREAM);
        }
    }

    public static class ArmorHud extends Module {
        public ArmorHud() {
            super("ArmorHUD", "Броня и прочность", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            if (mc.player == null) return;
            EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
            int x = w - 28, y = h / 2 - 50;
            for (EquipmentSlot slot : slots) {
                ItemStack st = mc.player.getEquippedStack(slot);
                if (st.isEmpty()) continue;
                Draw.round(c, x, y, 22, 22, 4, Theme.DARK);
                c.drawItem(st, x + 3, y + 3);
                if (st.isDamageable()) {
                    float frac = 1f - (float) st.getDamage() / Math.max(1, st.getMaxDamage());
                    Draw.rect(c, x + 3, y + 19, (int) (16 * frac), 2, Draw.lerp(0xFFFF4040, 0xFF60E060, frac));
                }
                y += 24;
            }
        }
    }

    public static class FeatureList extends Module {
        public FeatureList() {
            super("FeatureList", "Список включённых модулей", Category.HUD);
        }

        @Override
        public void onHud(DrawContext c, int w, int h) {
            TextRenderer tr = mc.textRenderer;
            List<Module> on = new ArrayList<>();
            for (Module m : ModuleManager.ALL) if (m.isEnabled() && m != this) on.add(m);
            on.sort(Comparator.comparingInt((Module m) -> -tr.getWidth(m.name)));
            int y = 6;
            for (int i = 0; i < on.size(); i++) {
                String n = on.get(i).name;
                int tw = tr.getWidth(n);
                int x = w - tw - 10;
                Draw.round(c, x - 3, y - 1, tw + 8, 11, 3, Theme.DARK);
                Draw.rect(c, w - 5, y - 1, 2, 11, Draw.lerp(Theme.A1, Theme.A2, on.size() <= 1 ? 0f : (float) i / (on.size() - 1)));
                c.drawTextWithShadow(tr, n, x, y, Theme.CREAM);
                y += 12;
            }
        }
    }

    // ============================================================ RENDER

    public static class Trails extends Module {
        private final Setting type = mode("Частицы", 0, PARTICLE_NAMES);
        private final Setting amount = num("Количество", 2, 1, 6, 1);
        private final Random rnd = new Random();

        public Trails() {
            super("Trails", "Шлейф частиц за персонажем при движении", Category.RENDER);
        }

        @Override
        public void onTick() {
            if (mc.player == null || mc.world == null || Stats.speed < 0.6) return;
            ParticleEffect fx = particle(type.getIndex());
            for (int i = 0; i < amount.getInt(); i++) {
                mc.world.addParticle(fx, mc.player.getX() + (rnd.nextDouble() - 0.5) * 0.4, mc.player.getY() + 0.05,
                        mc.player.getZ() + (rnd.nextDouble() - 0.5) * 0.4, 0, 0.01, 0);
            }
        }
    }

    public static class JumpCircles extends Module {
        private static final class Ring {
            final double x, y, z;
            int age;
            Ring(double x, double y, double z) { this.x = x; this.y = y; this.z = z; }
        }

        private final Setting type = mode("Частицы", 0, PARTICLE_NAMES);
        private final List<Ring> rings = new ArrayList<>();
        private boolean wasOnGround;

        public JumpCircles() {
            super("JumpCircles", "Расходящиеся круги в месте прыжка", Category.RENDER);
        }

        @Override
        public void onTick() {
            if (mc.player == null || mc.world == null) return;
            boolean ground = mc.player.isOnGround();
            if (wasOnGround && !ground && mc.player.getVelocity().y > 0.1) {
                rings.add(new Ring(mc.player.getX(), mc.player.getY() + 0.02, mc.player.getZ()));
            }
            wasOnGround = ground;
            ParticleEffect fx = particle(type.getIndex());
            for (Iterator<Ring> it = rings.iterator(); it.hasNext(); ) {
                Ring r = it.next();
                double radius = 0.3 + r.age * 0.18;
                int pts = Math.max(16, (int) (radius * 18));
                for (int k = 0; k < pts; k++) {
                    double a = Math.PI * 2 * k / pts;
                    mc.world.addParticle(fx, r.x + Math.cos(a) * radius, r.y, r.z + Math.sin(a) * radius, 0, 0.004, 0);
                }
                if (++r.age > 14) it.remove();
            }
        }
    }

    public static class ChinaHat extends Module {
        private final Setting type = mode("Частицы", 0, PARTICLE_NAMES);
        private final Setting firstPerson = bool("В первом лице", false);
        private final Random rnd = new Random();

        public ChinaHat() {
            super("ChinaHat", "Светящаяся шляпа из частиц над головой", Category.RENDER);
        }

        @Override
        public void onTick() {
            if (mc.player == null || mc.world == null) return;
            if (mc.options.getPerspective().isFirstPerson() && !firstPerson.getBool()) return;
            ParticleEffect fx = particle(type.getIndex());
            double base = mc.player.getEyeY() + 0.2;
            for (int i = 0; i < 5; i++) {
                double f = rnd.nextDouble();
                double r = 0.6 * (1 - f);
                double a = rnd.nextDouble() * Math.PI * 2;
                mc.world.addParticle(fx, mc.player.getX() + Math.cos(a) * r, base + f * 0.35, mc.player.getZ() + Math.sin(a) * r, 0, 0, 0);
            }
        }
    }

    public static class FullBright extends Module {
        private int timer;

        public FullBright() {
            super("FullBright", "Яркая картинка в темноте", Category.RENDER);
        }

        @Override
        public void onTick() {
            if (mc.player == null) return;
            if (timer-- <= 0) {
                timer = 100;
                mc.player.addStatusEffect(new StatusEffectInstance(StatusEffects.NIGHT_VISION, 600, 0, false, false, false));
            }
        }

        @Override
        public void onDisable() {
            timer = 0;
            if (mc.player != null) mc.player.removeStatusEffect(StatusEffects.NIGHT_VISION);
        }
    }

    public static class Zoom extends Module {
        private final Setting fov = num("FOV при зуме", 30, 30, 70, 1);
        private boolean zooming;
        private int saved;

        public Zoom() {
            super("Zoom", "Приближение, пока зажата клавиша C", Category.RENDER);
        }

        @Override
        public void onTick() {
            boolean held = BeeVisual.ZOOM_KEY != null && BeeVisual.ZOOM_KEY.isPressed() && mc.currentScreen == null;
            if (held) {
                if (!zooming) {
                    saved = mc.options.getFov().getValue();
                    zooming = true;
                }
                mc.options.getFov().setValue((int) fov.getNum());
            } else if (zooming) {
                mc.options.getFov().setValue(saved);
                zooming = false;
            }
        }

        @Override
        public void onDisable() {
            if (zooming) {
                mc.options.getFov().setValue(saved);
                zooming = false;
            }
        }
    }

    // ============================================================ WORLD

    public static class WeatherControl extends Module {
        public WeatherControl() {
            super("WeatherControl", "Отключает дождь и грозу (больше FPS)", Category.WORLD);
        }
    }

    public static class Ambience extends Module {
        private final Setting time = num("Время суток", 18000, 0, 24000, 500);

        public Ambience() {
            super("Ambience", "Своё время суток только у тебя на экране", Category.WORLD);
        }

        @Override
        public void onTick() {
            if (mc.world != null) mc.world.setTimeOfDay((long) time.getNum());
        }
    }

    public static class SnowGround extends Module {
        private final Setting radius = num("Радиус", 14, 6, 24, 1);
        private final Setting density = num("Густота", 5, 1, 10, 1);
        private final Setting lying = bool("Лежащий снег", true);
        private final Setting sparkle = bool("Блёстки", true);
        private final Setting windOn = bool("Ветер", true);
        private final Setting puff = bool("Пух при ходьбе", true);
        private final Random rnd = new Random();
        private int tick;

        public SnowGround() {
            super("SnowGround", "Красивый снег: падает, лежит, блестит и взлетает из-под ног", Category.WORLD);
        }

        @Override
        public void onTick() {
            var w = mc.world;
            var p = mc.player;
            if (w == null || p == null) return;
            tick++;
            double rad = radius.getNum();
            int tries = density.getInt() * 3;
            double wind = windOn.getBool() ? Math.sin(tick / 160.0) * 0.03 : 0.0;
            for (int i = 0; i < tries; i++) {
                double x = p.getX() + (rnd.nextDouble() * 2 - 1) * rad;
                double z = p.getZ() + (rnd.nextDouble() * 2 - 1) * rad;
                int top = w.getTopY(Heightmap.Type.MOTION_BLOCKING, (int) Math.floor(x), (int) Math.floor(z));
                if (top > p.getY() + 3) continue; // roof above: skip
                if (i % 2 == 0) {
                    w.addParticle(ParticleTypes.SNOWFLAKE, x, top + 3 + rnd.nextDouble() * 7, z, wind, -0.03 - rnd.nextDouble() * 0.03, wind * 0.6);
                }
                if (lying.getBool() && rnd.nextInt(3) == 0) {
                    w.addParticle(ParticleTypes.SNOWFLAKE, x, top + 0.04, z, 0, 0, 0);
                }
                if (sparkle.getBool() && rnd.nextInt(6) == 0) {
                    w.addParticle(ParticleTypes.ELECTRIC_SPARK, x, top + 0.1, z, 0, 0, 0);
                }
            }
            if (puff.getBool() && p.isOnGround() && Stats.speed > 1.0) {
                for (int k = 0; k < 2; k++) {
                    w.addParticle(ParticleTypes.CLOUD, p.getX() + (rnd.nextDouble() - 0.5) * 0.4, p.getY() + 0.1, p.getZ() + (rnd.nextDouble() - 0.5) * 0.4,
                            (rnd.nextDouble() - 0.5) * 0.05, 0.04, (rnd.nextDouble() - 0.5) * 0.05);
                }
            }
        }
    }
}
