The two calls differ only in which version they resolve. The documentation lists the forms side by side. `weave.ref([NAME])` retrieves the `:latest` version of an object and requires calling `weave.init(...)`. `weave.ref([NAME]:[VERSION])` retrieves the specified version and also requires `weave.init(...)`.

So `weave.ref("support_prompt:v3").get()` is pinned. It always returns version 3, no matter what you publish later. `weave.ref("support_prompt").get()` follows the `latest` alias. Every object automatically has a `:latest` alias that points to the most recent version, which means the result changes each time you publish a new version of `support_prompt`. For anything where reproducibility matters, such as an evaluation or a production deployment, pin a version or use a custom alias.

The part after the colon doesn't have to be a `vN` number. It can be a version hash, a string like `v0` or `v1`, or an alias, and you can create your own aliases, for example `weave.ref("support_prompt:production")`. An alias resolves to a single version and can be moved to a different version at any time, which makes it useful for stable references like `production` or `staging`.

**Do you need `weave.init`?** For both short forms, yes. A bare name like `support_prompt` doesn't say which team or project it belongs to, so `weave.init("team/project")` supplies that context:

```python
import weave

weave.init("my-team/my-project")
pinned = weave.ref("support_prompt:v3").get()   # always v3
newest = weave.ref("support_prompt").get()      # whatever :latest points to now
```

**Does a fully qualified URI change that?** Yes. A fully qualified ref has the form `weave:///[YOUR-TEAM-NAME]/[YOUR-PROJECT-NAME]/object/[OBJECT-NAME]:[OBJECT-VERSION]`. Because the team and project are part of the URI, `weave.ref([FULLY-QUALIFIED-REF-URI])` retrieves the object at that location and doesn't require calling `weave.init()`:

```python
import weave

prompt = weave.ref("weave:///my-team/my-project/object/support_prompt:v3").get()
```

The same latest-versus-pinned distinction still applies inside the URI. A version or alias after the colon determines what you get.

Two small notes. The `docs.wandb.ai/weave` link now redirects to CoreWeave's documentation site, which is where these details come from. Also, this ref-and-get workflow is Python-only for now: the docs say the feature isn't available in TypeScript yet.