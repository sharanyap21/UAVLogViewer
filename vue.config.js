module.exports = {
  chainWebpack: config => {
    config.module
      .rule('avif')
      .test(/\.avif$/)
      .use('file-loader')
      .loader('file-loader')
      .options({
        name: 'assets/[name].[hash:8].[ext]'
      })
    config.module
      .rule('webp')
      .test(/\.webp$/)
      .use('file-loader')
      .loader('file-loader')
      .options({
        name: 'assets/[name].[hash:8].[ext]'
      })
  }
} 