package dev.beevisual.mixin;

import dev.beevisual.module.ModuleManager;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** WeatherControl: client-side rain / thunder strength = 0 while the module is on. */
@Mixin(World.class)
public abstract class WorldMixin {
    @Inject(method = "getRainGradient", at = @At("HEAD"), cancellable = true, require = 0)
    private void beevisual$rain(float delta, CallbackInfoReturnable<Float> cir) {
        World self = (World) (Object) this;
        if (self.isClient() && ModuleManager.WEATHER != null && ModuleManager.WEATHER.isEnabled()) {
            cir.setReturnValue(0.0f);
        }
    }

    @Inject(method = "getThunderGradient", at = @At("HEAD"), cancellable = true, require = 0)
    private void beevisual$thunder(float delta, CallbackInfoReturnable<Float> cir) {
        World self = (World) (Object) this;
        if (self.isClient() && ModuleManager.WEATHER != null && ModuleManager.WEATHER.isEnabled()) {
            cir.setReturnValue(0.0f);
        }
    }
}
