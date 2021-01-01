# sm-morpher

Blender Addon: Create StaticMesh morph

## 概要

StaticMesh の UV（ch1+ch2）を使用して、StaticMesh に擬似的な MorphTarget の機能をもたせることを目的としたアドオン

## インストール

Blender の Preference > Addon で、 `staticmeshmorpher.py` を指定してインストールする

## 使用方法

埋め込み先のオブジェクトを `Original Object` に、変形したオブジェクトを `MorphTarget1` に指定して、 `Pack MorphTarget` を実行する

![使用方法](https://github.com/t-sumisaki/sm-morpher/blob/images/sm-morpher_usage.png)

実行後は通常通り FBXExport する

## UE4 での使用方法

通常の StaticMesh と同様に Import する

- `Generate Lightmap UVs` は外しておく
- `Store Morph1 Normals` の設定を ON にしている場合は、VertexColor の Import を有効にする

UnrealEngine ４の StaticMeshMorphTarget の Material を参考に、Morph 情報を引き出す Material を作成する

https://docs.unrealengine.com/ja/WorkingWithContent/Types/StaticMeshes/MorphTargets/index.html

![Material例](https://github.com/t-sumisaki/sm-morpher/blob/images/sm-morpher-ue4mat.png)

## 現状の問題点

- ハードサーフェースモデルの場合、Morph1 の Normal が期待通りに動かない

## トラブルシューティング

- Morph1 が思い通りに動かない
  - Import 時の設定で `Generate Lightmap UVs` が入っている場合、UV 情報が上書きされて Morph 情報が欠損する場合がある  
    この Addon は UV1 ～ 3 までを使用して Morph 情報を埋め込むので、それらのいずれかが上書きされると正しく動かなくなる  
    LightmapUV を使用する場合、使用する Morph が 1 つであれば、UV1 を使用すること  
    (Morph1 が UV2 ～ 3、Morph2 が UV1 ～ 2 を使用している)
